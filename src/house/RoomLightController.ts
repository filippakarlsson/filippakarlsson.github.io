import {
  Color,
  MathUtils,
  Mesh,
  MeshStandardMaterial,
  Object3D,
  PointLight,
} from 'three';
import { ROOMS, ROOM_IDS, type RoomId } from '../rooms';

interface RuntimeLight {
  light: PointLight;
  roomId: RoomId;
  targetIntensity: number;
}

interface EmissiveBinding {
  material: MeshStandardMaterial;
  roomId: RoomId;
  targetIntensity: number;
}

export class RoomLightController {
  private readonly runtimeLights: RuntimeLight[] = [];
  private readonly emissiveBindings: EmissiveBinding[] = [];
  private activeRoom: RoomId | null = null;

  constructor(private readonly model: Object3D) {
    this.buildRuntimeLights();
  }

  setActiveRoom(roomId: RoomId | null): boolean {
    if (this.activeRoom === roomId) return false;
    this.activeRoom = roomId;
    return true;
  }

  update(deltaSeconds: number): boolean {
    let isAnimating = false;

    for (const binding of this.runtimeLights) {
      const isActive = binding.roomId === this.activeRoom;
      const target = isActive ? binding.targetIntensity : 0;
      if (isActive) binding.light.visible = true;
      const next = MathUtils.damp(binding.light.intensity, target, 10, deltaSeconds);
      if (Math.abs(next - target) > 0.02) {
        binding.light.intensity = next;
        isAnimating = true;
      } else {
        binding.light.intensity = target;
      }
      if (!isActive && binding.light.intensity === 0) {
        binding.light.visible = false;
      }
    }

    for (const binding of this.emissiveBindings) {
      const target = binding.roomId === this.activeRoom ? binding.targetIntensity : 0;
      const next = MathUtils.damp(
        binding.material.emissiveIntensity,
        target,
        11,
        deltaSeconds,
      );
      if (Math.abs(next - target) > 0.002) {
        binding.material.emissiveIntensity = next;
        isAnimating = true;
      } else {
        binding.material.emissiveIntensity = target;
      }
    }

    return isAnimating;
  }

  getIntensities(): Record<RoomId, number> {
    return ROOM_IDS.reduce<Record<RoomId, number>>((result, roomId) => {
      result[roomId] = this.runtimeLights
        .filter((binding) => binding.roomId === roomId)
        .reduce((sum, binding) => sum + binding.light.intensity, 0);
      return result;
    }, {} as Record<RoomId, number>);
  }

  private buildRuntimeLights(): void {
    const anchors: Object3D[] = [];
    this.model.traverse((object) => {
      if (object.userData.runtimeLight === 'point') anchors.push(object);
    });

    for (const anchor of anchors) {
      const roomId = anchor.userData.roomId;
      if (!this.isRoom(roomId)) continue;

      const isMain = anchor.name === `${roomId.toUpperCase()}_HOVER_LIGHT`;
      const sourceEnergy = Number(anchor.userData.hover_target_energy ?? (isMain ? 520 : 90));
      const targetIntensity = sourceEnergy * 0.12;
      const lightColor = String(anchor.userData.lightColor ?? ROOMS[roomId].lightColor);
      const light = new PointLight(lightColor, 0, isMain ? 4.6 : 2.8, 2);
      light.name = `${anchor.name}_RUNTIME`;
      light.visible = false;
      light.position.copy(anchor.getWorldPosition(light.position));
      this.model.parent?.add(light);
      this.runtimeLights.push({ light, roomId, targetIntensity });

      this.bindEmissiveObject(
        anchor.userData.shade_object,
        roomId,
        Number(anchor.userData.hover_target_emission ?? (isMain ? 2.35 : 1.2)),
        lightColor,
      );
      this.bindEmissiveObject(
        anchor.userData.outer_shade_object,
        roomId,
        Number(anchor.userData.outer_shade_emission ?? 0.7),
        lightColor,
      );
    }
  }

  private bindEmissiveObject(
    objectName: unknown,
    roomId: RoomId,
    targetIntensity: number,
    lightColor: string,
  ): void {
    if (typeof objectName !== 'string') return;
    const object = this.model.getObjectByName(objectName);
    if (!(object instanceof Mesh)) return;

    const materials = Array.isArray(object.material) ? object.material : [object.material];
    const cloned = materials.map((material) => material.clone());
    object.material = Array.isArray(object.material) ? cloned : cloned[0];

    for (const material of cloned) {
      if (!(material instanceof MeshStandardMaterial)) continue;
      material.emissive = new Color(lightColor);
      material.emissiveIntensity = 0;
      this.emissiveBindings.push({ material, roomId, targetIntensity });
    }
  }

  private isRoom(value: unknown): value is RoomId {
    return typeof value === 'string' && ROOM_IDS.includes(value as RoomId);
  }
}
