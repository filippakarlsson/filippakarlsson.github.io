import type { HouseExperience } from './house/HouseExperience';
import type { RoomId } from './rooms';
import type { RoomView } from './RoomView';

export type TransitionPhase = 'overview' | 'zooming-in' | 'entering-page' | 'project-page' | 'returning';

const wait = (duration: number): Promise<void> => new Promise((resolve) => window.setTimeout(resolve, duration));

export class PageTransitionController {
  private phase: TransitionPhase = 'overview';
  private selectedRoom: RoomId | null = null;

  constructor(
    private readonly experience: HouseExperience,
    private readonly roomView: RoomView,
    private readonly overlay: HTMLElement,
    private readonly houseStage: HTMLElement,
  ) {}

  getPhase(): TransitionPhase {
    return this.phase;
  }

  async enterRoom(roomId: RoomId): Promise<void> {
    if (this.phase !== 'overview') return;
    this.selectedRoom = roomId;
    this.setPhase('zooming-in');
    document.body.classList.add('portfolio-is-transitioning');

    try {
      await this.experience.focusRoom(roomId);
      this.setPhase('entering-page');
      await this.coverWithWhite(560);
      await wait(this.motionDuration(180));

      this.roomView.show(roomId);
      document.body.classList.add('project-is-open');
      this.houseStage.setAttribute('aria-hidden', 'true');
      this.houseStage.hidden = true;
      this.experience.pauseRendering();

      await Promise.all([
        this.revealFromWhite(680),
        this.animateRoomView([{ opacity: 0 }, { opacity: 1 }], 680),
      ]);

      this.setPhase('project-page');
      this.roomView.focusBackButton();
    } catch (error) {
      this.recoverOverview();
      throw error;
    } finally {
      document.body.classList.remove('portfolio-is-transitioning');
    }
  }

  async returnToHouse(): Promise<void> {
    if (this.phase !== 'project-page' || !this.selectedRoom) return;
    const roomId = this.selectedRoom;
    this.setPhase('returning');
    document.body.classList.add('portfolio-is-transitioning');

    try {
      await Promise.all([
        this.coverWithWhite(500),
        this.animateRoomView([{ opacity: 1 }, { opacity: 0 }], 420),
      ]);

      this.roomView.hide();
      document.body.classList.remove('project-is-open');
      this.houseStage.hidden = false;
      this.houseStage.setAttribute('aria-hidden', 'false');
      this.experience.prepareRoomReturn(roomId);
      await wait(this.motionDuration(180));
      await this.revealFromWhite(520);
      await this.experience.returnToOverview();

      this.selectedRoom = null;
      this.setPhase('overview');
      document.title = 'Portfolio House — Interaction Prototype';
    } finally {
      document.body.classList.remove('portfolio-is-transitioning');
    }
  }

  private setPhase(phase: TransitionPhase): void {
    this.phase = phase;
    document.body.dataset.transitionPhase = phase;
  }

  private async coverWithWhite(duration: number): Promise<void> {
    this.overlay.hidden = false;
    this.overlay.setAttribute('aria-hidden', 'false');
    this.overlay.style.pointerEvents = 'auto';
    await this.animate(this.overlay, [{ opacity: 0 }, { opacity: 1 }], duration);
    this.overlay.style.opacity = '1';
  }

  private async revealFromWhite(duration: number): Promise<void> {
    await this.animate(this.overlay, [{ opacity: 1 }, { opacity: 0 }], duration);
    this.overlay.style.opacity = '0';
    this.overlay.style.pointerEvents = 'none';
    this.overlay.setAttribute('aria-hidden', 'true');
    this.overlay.hidden = true;
  }

  private async animateRoomView(keyframes: Keyframe[], duration: number): Promise<void> {
    await this.animate(this.roomViewElement(), keyframes, duration);
  }

  private roomViewElement(): HTMLElement {
    const element = document.querySelector<HTMLElement>('#room-view');
    if (!element) throw new Error('The room view is unavailable.');
    return element;
  }

  private async animate(element: HTMLElement, keyframes: Keyframe[], duration: number): Promise<void> {
    const animation = element.animate(keyframes, {
      duration: this.motionDuration(duration),
      easing: 'cubic-bezier(0.22, 1, 0.36, 1)',
      fill: 'forwards',
    });
    await animation.finished;
  }

  private motionDuration(duration: number): number {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches ? Math.min(duration, 120) : duration;
  }

  private recoverOverview(): void {
    this.overlay.hidden = true;
    this.roomView.hide();
    this.houseStage.hidden = false;
    document.body.classList.remove('project-is-open');
    this.experience.prepareRoomReturn(this.selectedRoom!);
    void this.experience.returnToOverview();
    this.selectedRoom = null;
    this.setPhase('overview');
  }
}
