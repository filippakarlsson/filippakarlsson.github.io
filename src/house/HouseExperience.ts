import {
  ACESFilmicToneMapping,
  AmbientLight,
  Box3,
  DirectionalLight,
  HemisphereLight,
  Mesh,
  Object3D,
  OrthographicCamera,
  SRGBColorSpace,
  Scene,
  Vector3,
  WebGLRenderer,
} from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
import { ROOMS, ROOM_IDS, type RoomId } from '../rooms';
import { RoomInteractionController } from './RoomInteractionController';
import { RoomLightController } from './RoomLightController';
import { CameraTransitionController } from './CameraTransitionController';

export interface HouseState {
  ready: boolean;
  hoveredRoom: RoomId | null;
  selectedRoom: RoomId | null;
  interactionEnabled: boolean;
  rendering: boolean;
  cameraZoom: number;
  cameraPosition: [number, number, number] | null;
  hitboxCount: number;
  sourceMeshCount: number;
  finalMeshCount: number;
  mergedGroupCount: number;
  lightIntensities: Record<RoomId, number>;
}

export class HouseExperience {
  private readonly scene = new Scene();
  private readonly renderer: WebGLRenderer;
  private camera: OrthographicCamera | null = null;
  private interaction: RoomInteractionController | null = null;
  private lights: RoomLightController | null = null;
  private cameraTransitions: CameraTransitionController | null = null;
  private selectedRoom: RoomId | null = null;
  private rendering = false;
  private animationFrame: number | null = null;
  private lastFrameTime = performance.now();
  private lastDebugUpdate = 0;
  private modelMeshCount = 0;
  private renderedFrameCount = 0;
  private overviewFrustumCenterX = 0;

  constructor(
    private readonly canvas: HTMLCanvasElement,
    private readonly onHover: (roomId: RoomId | null) => void,
    private readonly onSelect: (roomId: RoomId) => void,
  ) {
    this.renderer = new WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: 'high-performance' });
    this.renderer.outputColorSpace = SRGBColorSpace;
    this.renderer.toneMapping = ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.12;
    this.renderer.setClearColor(0x000000, 0);
    this.scene.background = null;
  }

  async load(url: string): Promise<void> {
    const loader = new GLTFLoader();
    loader.setMeshoptDecoder(MeshoptDecoder);
    const gltf = await loader.loadAsync(url);
    const model = gltf.scene;
    model.name = 'PORTFOLIO_HOUSE';
    this.scene.add(model);

    model.traverse((object) => {
      if (object instanceof Mesh) this.modelMeshCount += 1;
    });
    this.prepareMaterials(model);
    this.addGlobalLighting();
    this.camera = this.resolveCamera(model);
    this.lights = new RoomLightController(model);
    this.interaction = new RoomInteractionController(this.canvas, this.camera, model, {
      onHover: (roomId) => {
        if (this.lights?.setActiveRoom(roomId)) this.resumeRendering();
        this.onHover(roomId);
      },
      onSelect: (roomId) => {
        this.selectedRoom = roomId;
        this.onSelect(roomId);
      },
    });
    this.cameraTransitions = new CameraTransitionController(
      this.camera,
      (roomId) => this.interaction?.getRoomViewBounds(roomId) ?? null,
      this.renderFrame,
    );

    if (this.interaction.getHitboxCount() !== ROOM_IDS.length) {
      throw new Error(`Expected ${ROOM_IDS.length} room hitboxes, found ${this.interaction.getHitboxCount()}.`);
    }

    this.resize();
    window.addEventListener('resize', this.resize);
    document.addEventListener('visibilitychange', this.onVisibilityChange);
    this.canvas.dataset.ready = 'true';
    this.canvas.dataset.hitboxCount = String(this.interaction.getHitboxCount());
    this.updateRoomPositions();
    this.renderOnce();
  }

  async focusRoom(roomId: RoomId): Promise<void> {
    if (!this.cameraTransitions || !this.interaction) return;
    this.interaction.setEnabled(false);
    this.selectedRoom = roomId;
    if (this.lights?.setActiveRoom(roomId)) this.resumeRendering();
    await this.cameraTransitions.focusRoom(roomId);
    this.renderOnce();
  }

  pauseRendering(): void {
    this.rendering = false;
    if (this.animationFrame !== null) cancelAnimationFrame(this.animationFrame);
    this.animationFrame = null;
    this.writeDebugState();
  }

  resumeRendering(): void {
    if (this.rendering) return;
    this.rendering = true;
    this.lastFrameTime = performance.now();
    this.animationFrame = requestAnimationFrame(this.animate);
    this.writeDebugState();
  }

  prepareRoomReturn(roomId: RoomId): void {
    this.selectedRoom = roomId;
    this.interaction?.setEnabled(false);
    if (this.lights?.setActiveRoom(roomId)) this.resumeRendering();
    this.cameraTransitions?.restoreFocusedRoom(roomId);
    this.resumeRendering();
    this.renderOnce();
  }

  async returnToOverview(): Promise<void> {
    if (!this.cameraTransitions) return;
    await this.cameraTransitions.returnToOverview();
    this.selectedRoom = null;
    if (this.lights?.setActiveRoom(null)) this.resumeRendering();
    this.interaction?.setEnabled(true);
    this.onHover(null);
    this.updateRoomPositions();
    this.renderOnce();
  }

  getState(): HouseState {
    return {
      ready: this.interaction !== null,
      hoveredRoom: this.interaction?.getHoveredRoom() ?? null,
      selectedRoom: this.selectedRoom,
      interactionEnabled: this.interaction?.isEnabled() ?? false,
      rendering: this.rendering,
      cameraZoom: this.camera?.zoom ?? 0,
      cameraPosition: this.camera
        ? [this.camera.position.x, this.camera.position.y, this.camera.position.z]
        : null,
      hitboxCount: this.interaction?.getHitboxCount() ?? 0,
      sourceMeshCount: this.modelMeshCount,
      finalMeshCount: this.modelMeshCount,
      mergedGroupCount: 0,
      lightIntensities: this.lights?.getIntensities() ?? this.emptyIntensities(),
    };
  }

  getRoomScreenPosition(roomId: RoomId): { x: number; y: number } | null {
    return this.interaction?.getRoomScreenPosition(roomId) ?? null;
  }

  private readonly resize = (): void => {
    if (!this.camera) return;
    const width = Math.max(1, this.canvas.clientWidth);
    const height = Math.max(1, this.canvas.clientHeight);
    const aspect = width / height;
    const centerStrength = Math.min(1, Math.max(0, (1120 - width) / 300));
    const mobileCropStrength = Math.min(1, Math.max(0, (680 - width) / 120));
    const portraitFit = 7.3;
    const horizontalFit = 5.4 - 0.7 * mobileCropStrength;
    const widthFit = horizontalFit / aspect;
    const halfHeight = Math.max(portraitFit, widthFit);
    const halfWidth = halfHeight * aspect;
    const mobileVerticalOffset = 0.95 * mobileCropStrength;

    if (this.selectedRoom === null) {
      const roomsCenter = this.interaction?.getRoomsCenter();
      if (roomsCenter) {
        this.camera.updateMatrixWorld(true);
        this.overviewFrustumCenterX = this.camera.worldToLocal(roomsCenter.clone()).x * centerStrength;
      }
    }

    this.camera.left = this.overviewFrustumCenterX - halfWidth;
    this.camera.right = this.overviewFrustumCenterX + halfWidth;
    this.camera.top = halfHeight + mobileVerticalOffset;
    this.camera.bottom = -halfHeight + mobileVerticalOffset;
    this.camera.updateProjectionMatrix();
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setSize(width, height, false);
    this.updateRoomPositions();
    this.renderOnce();
  };

  private readonly onVisibilityChange = (): void => {
    if (document.hidden) {
      this.pauseRendering();
      return;
    }
    this.resumeRendering();
  };

  private readonly animate = (now: number): void => {
    if (!this.rendering) return;
    const delta = Math.min((now - this.lastFrameTime) / 1000, 0.05);
    this.lastFrameTime = now;
    const lightsAreAnimating = this.lights?.update(delta) ?? false;
    this.renderFrame();
    if (now - this.lastDebugUpdate > 100) {
      this.writeDebugState();
      this.lastDebugUpdate = now;
    }
    if (lightsAreAnimating) {
      this.animationFrame = requestAnimationFrame(this.animate);
      return;
    }

    this.rendering = false;
    this.animationFrame = null;
    this.writeDebugState();
  };

  private readonly renderOnce = (): void => {
    this.renderFrame();
    this.updateRoomPositions();
    this.writeDebugState();
  };

  private readonly renderFrame = (): void => {
    if (!this.camera) return;
    this.renderer.render(this.scene, this.camera);
    this.renderedFrameCount += 1;
  };

  private writeDebugState(): void {
    const state = this.getState();
    this.canvas.dataset.hoveredRoom = state.hoveredRoom ?? '';
    this.canvas.dataset.selectedRoom = state.selectedRoom ?? '';
    this.canvas.dataset.interactionEnabled = String(state.interactionEnabled);
    this.canvas.dataset.rendering = String(state.rendering);
    this.canvas.dataset.cameraZoom = state.cameraZoom.toFixed(4);
    this.canvas.dataset.cameraPosition = JSON.stringify(state.cameraPosition);
    this.canvas.dataset.lightIntensities = JSON.stringify(state.lightIntensities);
    this.canvas.dataset.sourceMeshes = String(state.sourceMeshCount);
    this.canvas.dataset.finalMeshes = String(state.finalMeshCount);
    this.canvas.dataset.mergedGroups = String(state.mergedGroupCount);
    this.canvas.dataset.drawCalls = String(this.renderer.info.render.calls);
    this.canvas.dataset.triangles = String(this.renderer.info.render.triangles);
    this.canvas.dataset.renderedFrames = String(this.renderedFrameCount);
  }

  private updateRoomPositions(): void {
    if (!this.interaction) return;
    const positions = ROOM_IDS.reduce<Partial<Record<RoomId, { x: number; y: number }>>>((result, roomId) => {
      const position = this.interaction?.getRoomScreenPosition(roomId);
      if (position) result[roomId] = position;
      return result;
    }, {});
    this.canvas.dataset.roomPositions = JSON.stringify(positions);
  }

  private resolveCamera(model: Object3D): OrthographicCamera {
    const authored = model.getObjectByName('REFERENCE_FRONT_CAMERA');
    if (authored instanceof OrthographicCamera) return authored;

    const bounds = new Box3().setFromObject(model);
    const center = bounds.getCenter(new Vector3());
    const camera = new OrthographicCamera(-8, 8, 8, -8, 0.1, 100);
    camera.position.set(6.5, 27, 6.25);
    camera.lookAt(center);
    this.scene.add(camera);
    return camera;
  }

  private prepareMaterials(model: Object3D): void {
    model.traverse((object) => {
      if (!(object instanceof Mesh)) return;
      object.castShadow = false;
      object.receiveShadow = false;
    });
  }

  private addGlobalLighting(): void {
    this.scene.add(new AmbientLight('#fff8ef', 0.72));
    this.scene.add(new HemisphereLight('#fffaf2', '#c9ced1', 1.15));
    const key = new DirectionalLight('#ffe4c8', 2.3);
    key.position.set(-5, -8, 12);
    this.scene.add(key);
  }

  private emptyIntensities(): Record<RoomId, number> {
    return ROOM_IDS.reduce<Record<RoomId, number>>((result, roomId) => {
      result[roomId] = 0;
      return result;
    }, {} as Record<RoomId, number>);
  }
}

export function roomSummary(roomId: RoomId): string {
  return `${ROOMS[roomId].label} — ${ROOMS[roomId].description}`;
}
