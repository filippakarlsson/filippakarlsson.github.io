import {
  Box3,
  MathUtils,
  OrthographicCamera,
  Vector3,
} from 'three';
import type { RoomId } from '../rooms';

export interface RoomViewBounds {
  center: Vector3;
  bounds: Box3;
}

interface CameraPose {
  position: Vector3;
  zoom: number;
}

const easeInOutCubic = (value: number): number => (
  value < 0.5
    ? 4 * value * value * value
    : 1 - Math.pow(-2 * value + 2, 3) / 2
);

export class CameraTransitionController {
  private readonly overviewPose: CameraPose;
  private focusedPose: CameraPose | null = null;
  private focusedRoom: RoomId | null = null;
  private animationFrame: number | null = null;

  constructor(
    private readonly camera: OrthographicCamera,
    private readonly getRoomViewBounds: (roomId: RoomId) => RoomViewBounds | null,
    private readonly onUpdate: () => void,
  ) {
    this.overviewPose = this.capturePose();
  }

  async focusRoom(roomId: RoomId, duration = 1500): Promise<void> {
    const pose = this.createFocusedPose(roomId);
    if (!pose) throw new Error(`Could not resolve a camera target for ${roomId}.`);

    this.focusedRoom = roomId;
    this.focusedPose = pose;
    await this.animateTo(pose, duration);
  }

  restoreFocusedRoom(roomId: RoomId): void {
    if (this.focusedRoom !== roomId || !this.focusedPose) {
      this.focusedRoom = roomId;
      this.focusedPose = this.createFocusedPose(roomId);
    }

    if (!this.focusedPose) return;
    this.applyPose(this.focusedPose);
  }

  async returnToOverview(duration = 1500): Promise<void> {
    await this.animateTo(this.overviewPose, duration);
  }

  private createFocusedPose(roomId: RoomId): CameraPose | null {
    const room = this.getRoomViewBounds(roomId);
    if (!room) return null;

    this.camera.updateMatrixWorld(true);
    const right = new Vector3(1, 0, 0).applyQuaternion(this.camera.quaternion).normalize();
    const up = new Vector3(0, 1, 0).applyQuaternion(this.camera.quaternion).normalize();
    const offset = room.center.clone().sub(this.overviewPose.position);
    const position = this.overviewPose.position
      .clone()
      .addScaledVector(right, offset.dot(right))
      .addScaledVector(up, offset.dot(up));

    const size = room.bounds.getSize(new Vector3());
    const corners = [
      new Vector3(room.bounds.min.x, room.bounds.min.y, room.bounds.min.z),
      new Vector3(room.bounds.min.x, room.bounds.min.y, room.bounds.max.z),
      new Vector3(room.bounds.min.x, room.bounds.max.y, room.bounds.min.z),
      new Vector3(room.bounds.min.x, room.bounds.max.y, room.bounds.max.z),
      new Vector3(room.bounds.max.x, room.bounds.min.y, room.bounds.min.z),
      new Vector3(room.bounds.max.x, room.bounds.min.y, room.bounds.max.z),
      new Vector3(room.bounds.max.x, room.bounds.max.y, room.bounds.min.z),
      new Vector3(room.bounds.max.x, room.bounds.max.y, room.bounds.max.z),
    ];

    let roomWidth = 0;
    let roomHeight = 0;
    for (const corner of corners) {
      const relative = corner.sub(room.center);
      roomWidth = Math.max(roomWidth, Math.abs(relative.dot(right)) * 2);
      roomHeight = Math.max(roomHeight, Math.abs(relative.dot(up)) * 2);
    }

    const baseWidth = this.camera.right - this.camera.left;
    const baseHeight = this.camera.top - this.camera.bottom;
    const widthZoom = (baseWidth * 0.58) / Math.max(roomWidth, size.x * 0.35, 0.01);
    const heightZoom = (baseHeight * 0.62) / Math.max(roomHeight, size.z * 0.35, 0.01);
    const zoom = MathUtils.clamp(
      Math.min(widthZoom, heightZoom),
      this.overviewPose.zoom * 2.85,
      this.overviewPose.zoom * 4.2,
    );

    return { position, zoom };
  }

  private animateTo(target: CameraPose, duration: number): Promise<void> {
    if (this.animationFrame !== null) cancelAnimationFrame(this.animationFrame);
    const start = this.capturePose();
    const startedAt = performance.now();
    const motionDuration = window.matchMedia('(prefers-reduced-motion: reduce)').matches
      ? Math.min(duration, 260)
      : duration;

    return new Promise((resolve) => {
      const step = (now: number): void => {
        const progress = Math.min((now - startedAt) / motionDuration, 1);
        const eased = easeInOutCubic(progress);
        this.camera.position.lerpVectors(start.position, target.position, eased);
        this.camera.zoom = MathUtils.lerp(start.zoom, target.zoom, eased);
        this.camera.updateProjectionMatrix();
        this.camera.updateMatrixWorld(true);
        this.onUpdate();

        if (progress < 1) {
          this.animationFrame = requestAnimationFrame(step);
          return;
        }

        this.animationFrame = null;
        this.applyPose(target);
        resolve();
      };

      this.animationFrame = requestAnimationFrame(step);
    });
  }

  private capturePose(): CameraPose {
    return {
      position: this.camera.position.clone(),
      zoom: this.camera.zoom,
    };
  }

  private applyPose(pose: CameraPose): void {
    this.camera.position.copy(pose.position);
    this.camera.zoom = pose.zoom;
    this.camera.updateProjectionMatrix();
    this.camera.updateMatrixWorld(true);
    this.onUpdate();
  }
}
