import {
  Box3,
  Camera,
  Mesh,
  Object3D,
  Raycaster,
  Vector2,
  Vector3,
} from 'three';
import { isRoomId, type RoomId } from '../rooms';
import type { RoomViewBounds } from './CameraTransitionController';

interface RoomInteractionCallbacks {
  onHover: (roomId: RoomId | null) => void;
  onSelect: (roomId: RoomId) => void;
}

export class RoomInteractionController {
  private readonly raycaster = new Raycaster();
  private readonly pointer = new Vector2();
  private readonly hitboxes = new Map<RoomId, Mesh>();
  private hoveredRoom: RoomId | null = null;
  private enabled = true;
  private pointerFrame: number | null = null;
  private pendingPointer: { x: number; y: number } | null = null;

  constructor(
    private readonly canvas: HTMLCanvasElement,
    private readonly camera: Camera,
    model: Object3D,
    private readonly callbacks: RoomInteractionCallbacks,
  ) {
    model.traverse((object) => {
      if (!(object instanceof Mesh) || object.userData.interaction !== 'room') return;
      const roomId = object.userData.roomId;
      if (!isRoomId(roomId)) return;

      object.material.visible = false;
      this.hitboxes.set(roomId, object);
    });

    this.canvas.addEventListener('pointermove', this.onPointerMove, { passive: true });
    this.canvas.addEventListener('pointerleave', this.onPointerLeave, { passive: true });
    this.canvas.addEventListener('click', this.onClick);
  }

  getHoveredRoom(): RoomId | null {
    return this.hoveredRoom;
  }

  getHitboxCount(): number {
    return this.hitboxes.size;
  }

  isEnabled(): boolean {
    return this.enabled;
  }

  setEnabled(enabled: boolean): void {
    if (this.enabled === enabled) return;
    this.enabled = enabled;
    this.canvas.classList.toggle('is-interaction-locked', !enabled);
    if (!enabled) {
      this.cancelPendingPointer();
      this.setHoveredRoom(null);
    }
  }

  getRoomViewBounds(roomId: RoomId): RoomViewBounds | null {
    const hitbox = this.hitboxes.get(roomId);
    if (!hitbox) return null;
    const bounds = new Box3().setFromObject(hitbox);
    return { bounds, center: bounds.getCenter(new Vector3()) };
  }

  getRoomsCenter(): Vector3 | null {
    if (this.hitboxes.size === 0) return null;

    const center = new Vector3();
    for (const hitbox of this.hitboxes.values()) {
      center.add(hitbox.getWorldPosition(new Vector3()));
    }
    return center.divideScalar(this.hitboxes.size);
  }

  getRoomScreenPosition(roomId: RoomId): { x: number; y: number } | null {
    const hitbox = this.hitboxes.get(roomId);
    if (!hitbox) return null;

    const worldPosition = hitbox.getWorldPosition(new Vector3());
    const projected = worldPosition.project(this.camera);
    const bounds = this.canvas.getBoundingClientRect();
    return {
      x: bounds.left + ((projected.x + 1) / 2) * bounds.width,
      y: bounds.top + ((1 - projected.y) / 2) * bounds.height,
    };
  }

  private readonly onPointerMove = (event: PointerEvent): void => {
    if (!this.enabled) return;
    this.pendingPointer = { x: event.clientX, y: event.clientY };
    if (this.pointerFrame !== null) return;

    this.pointerFrame = requestAnimationFrame(() => {
      this.pointerFrame = null;
      const pointer = this.pendingPointer;
      this.pendingPointer = null;
      if (!pointer || !this.enabled) return;
      this.setHoveredRoom(this.pickRoom(pointer.x, pointer.y));
    });
  };

  private readonly onPointerLeave = (): void => {
    this.cancelPendingPointer();
    this.setHoveredRoom(null);
  };

  private readonly onClick = (event: MouseEvent): void => {
    if (!this.enabled) return;
    const roomId = this.pickRoom(event.clientX, event.clientY);
    if (roomId) this.callbacks.onSelect(roomId);
  };

  private pickRoom(clientX: number, clientY: number): RoomId | null {
    if (!this.enabled) return null;
    const bounds = this.canvas.getBoundingClientRect();
    this.pointer.x = ((clientX - bounds.left) / bounds.width) * 2 - 1;
    this.pointer.y = -((clientY - bounds.top) / bounds.height) * 2 + 1;
    this.raycaster.setFromCamera(this.pointer, this.camera);

    const intersections = this.raycaster.intersectObjects([...this.hitboxes.values()], false);
    const roomId = intersections[0]?.object.userData.roomId;
    return isRoomId(roomId) ? roomId : null;
  }

  private setHoveredRoom(roomId: RoomId | null): void {
    if (this.hoveredRoom === roomId) return;
    this.hoveredRoom = roomId;
    this.canvas.classList.toggle('is-room-hovered', roomId !== null);
    this.callbacks.onHover(roomId);
  }

  private cancelPendingPointer(): void {
    if (this.pointerFrame !== null) cancelAnimationFrame(this.pointerFrame);
    this.pointerFrame = null;
    this.pendingPointer = null;
  }
}
