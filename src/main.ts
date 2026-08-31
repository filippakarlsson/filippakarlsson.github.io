import './styles.css';
import { HouseExperience, roomSummary } from './house/HouseExperience';
import { ROOM_IDS, ROOMS, type RoomId } from './rooms';
import { PageTransitionController, type TransitionPhase } from './PageTransitionController';
import { RoomView } from './RoomView';

declare global {
  interface Window {
    __HOUSE_DEBUG__?: {
      getState: () => ReturnType<HouseExperience['getState']>;
      getRoomScreenPosition: (roomId: RoomId) => { x: number; y: number } | null;
      rooms: readonly RoomId[];
      getTransitionPhase: () => TransitionPhase;
    };
  }
}

const canvas = document.querySelector<HTMLCanvasElement>('#house-canvas');
const loadingState = document.querySelector<HTMLElement>('#loading-state');
const errorState = document.querySelector<HTMLElement>('#error-state');
const errorDetail = document.querySelector<HTMLElement>('#error-detail');
const interactionStatus = document.querySelector<HTMLElement>('.interaction-status');
const statusEyebrow = document.querySelector<HTMLElement>('#status-eyebrow');
const statusRoom = document.querySelector<HTMLElement>('#status-room');
const menuTrigger = document.querySelector<HTMLButtonElement>('#menu-trigger');
const themeToggle = document.querySelector<HTMLButtonElement>('#theme-toggle');
const themeLabel = document.querySelector<HTMLElement>('[data-theme-label]');
const themeIcon = document.querySelector<HTMLElement>('[data-theme-icon]');
const infoOverlay = document.querySelector<HTMLElement>('#info-overlay');
const infoCloseButtons = document.querySelectorAll<HTMLButtonElement>('[data-info-close]');
const infoPageButtons = document.querySelectorAll<HTMLButtonElement>('[data-info-page]');
const infoPages = document.querySelectorAll<HTMLElement>('[data-info-content]');
const roomViewElement = document.querySelector<HTMLElement>('#room-view');
const transitionOverlay = document.querySelector<HTMLElement>('#white-transition');
const houseStage = document.querySelector<HTMLElement>('.house-stage');

if (!canvas || !loadingState || !errorState || !errorDetail || !interactionStatus || !statusEyebrow || !statusRoom || !menuTrigger || !themeToggle || !themeLabel || !themeIcon || !infoOverlay || !roomViewElement || !transitionOverlay || !houseStage) {
  throw new Error('The prototype shell is missing required elements.');
}

let experience: HouseExperience;
let pageTransition: PageTransitionController;
type InfoPage = 'about' | 'contact';
type Theme = 'day' | 'night';

const setTheme = (theme: Theme, persist = true): void => {
  const isNight = theme === 'night';
  document.documentElement.dataset.theme = theme;
  themeToggle.setAttribute('aria-pressed', String(isNight));
  themeToggle.setAttribute('aria-label', `Switch to ${isNight ? 'day' : 'night'} mode`);
  themeToggle.title = `Switch to ${isNight ? 'day' : 'night'} mode`;
  themeLabel.textContent = isNight ? 'Day' : 'Night';
  themeIcon.textContent = isNight ? '☀' : '☾';

  if (persist) {
    try {
      localStorage.setItem('portfolio-theme', theme);
    } catch {
      // The theme still works when storage is unavailable.
    }
  }
};

setTheme(document.documentElement.dataset.theme === 'night' ? 'night' : 'day', false);
themeToggle.addEventListener('click', () => {
  setTheme(document.documentElement.dataset.theme === 'night' ? 'day' : 'night');
});

const showInfoPage = (page: InfoPage): void => {
  for (const button of infoPageButtons) {
    const isCurrent = button.dataset.infoPage === page;
    if (isCurrent) button.setAttribute('aria-current', 'page');
    else button.removeAttribute('aria-current');
  }

  for (const content of infoPages) {
    content.hidden = content.dataset.infoContent !== page;
  }
};

const setInfoOpen = (isOpen: boolean): void => {
  menuTrigger.setAttribute('aria-expanded', String(isOpen));
  infoOverlay.setAttribute('aria-hidden', String(!isOpen));
  infoOverlay.inert = !isOpen;
  infoOverlay.classList.toggle('is-open', isOpen);
  document.body.classList.toggle('info-is-open', isOpen);

  if (isOpen) {
    showInfoPage('about');
    requestAnimationFrame(() => infoPageButtons[0]?.focus());
  } else {
    menuTrigger.focus();
  }
};

infoOverlay.inert = true;
menuTrigger.addEventListener('click', () => {
  setInfoOpen(menuTrigger.getAttribute('aria-expanded') !== 'true');
});

for (const button of infoCloseButtons) {
  button.addEventListener('click', () => setInfoOpen(false));
}

for (const button of infoPageButtons) {
  button.addEventListener('click', () => {
    const page = button.dataset.infoPage;
    if (page === 'about' || page === 'contact') showInfoPage(page);
  });
}

document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && menuTrigger.getAttribute('aria-expanded') === 'true') {
    setInfoOpen(false);
  }
});

const alignStatusToRoom = (roomId: RoomId | null): void => {
  if (!roomId) {
    interactionStatus.classList.remove('is-room-aligned');
    interactionStatus.style.removeProperty('--room-y');
    return;
  }

  const roomPosition = experience.getRoomScreenPosition(roomId);
  if (!roomPosition) return;

  interactionStatus.style.setProperty('--room-y', `${Math.round(roomPosition.y)}px`);
  interactionStatus.classList.add('is-room-aligned');
};

const showHover = (roomId: RoomId | null): void => {
  alignStatusToRoom(roomId);

  if (!roomId) {
    statusEyebrow.textContent = 'Explore the house';
    statusRoom.textContent = 'Move across a room';
    return;
  }

  statusEyebrow.textContent = ROOMS[roomId].description;
  statusRoom.textContent = ROOMS[roomId].label;
};

const showSelection = (roomId: RoomId): void => {
  alignStatusToRoom(roomId);
  statusEyebrow.textContent = 'Entering';
  statusRoom.textContent = roomSummary(roomId);
  window.dispatchEvent(new CustomEvent('portfolio-room-select', { detail: ROOMS[roomId] }));
  void pageTransition.enterRoom(roomId).catch((error: unknown) => {
    console.error('Room transition failed:', error);
  });
};

experience = new HouseExperience(canvas, showHover, showSelection);
const roomView = new RoomView(roomViewElement, () => {
  void pageTransition.returnToHouse().catch((error: unknown) => {
    console.error('Return transition failed:', error);
  });
});
pageTransition = new PageTransitionController(experience, roomView, transitionOverlay, houseStage);
window.__HOUSE_DEBUG__ = {
  getState: () => experience.getState(),
  getRoomScreenPosition: (roomId) => experience.getRoomScreenPosition(roomId),
  rooms: ROOM_IDS,
  getTransitionPhase: () => pageTransition.getPhase(),
};

experience
  .load('/models/house.glb')
  .then(() => {
    loadingState.hidden = true;
  })
  .catch((error: unknown) => {
    loadingState.hidden = true;
    errorState.hidden = false;
    errorDetail.textContent = error instanceof Error ? error.message : String(error);
    console.error('Portfolio house failed to load:', error);
  });
