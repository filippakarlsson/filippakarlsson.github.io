import './two-d.css';
import { ROOMS, type RoomId } from './rooms';

const FLOOR_ORDER: readonly RoomId[] = ['rooftop', 'studio', 'office', 'playroom', 'welcome', 'basement'];
const FLOOR_REGIONS: Record<RoomId, { top: number; height: number }> = {
  rooftop: { top: 6.7, height: 17.6 },
  studio: { top: 25.0, height: 12.3 },
  office: { top: 38.1, height: 13.2 },
  playroom: { top: 52.2, height: 13.2 },
  welcome: { top: 66.3, height: 13.0 },
  basement: { top: 80.5, height: 14.7 },
};

const shell = document.querySelector<HTMLElement>('[data-house-shell]');
const floorMap = document.querySelector<HTMLElement>('[data-floor-map]');
const sheet = document.querySelector<HTMLElement>('[data-room-sheet]');
const statusNumber = document.querySelector<HTMLElement>('[data-room-number]');
const statusLabel = document.querySelector<HTMLElement>('[data-room-label]');
const statusDescription = document.querySelector<HTMLElement>('[data-room-description]');
const sheetEyebrow = document.querySelector<HTMLElement>('[data-sheet-eyebrow]');
const sheetTitle = document.querySelector<HTMLElement>('[data-sheet-title]');
const sheetDescription = document.querySelector<HTMLElement>('[data-sheet-description]');
const sheetProjects = document.querySelector<HTMLElement>('[data-sheet-projects]');

if (!shell || !floorMap || !sheet || !statusNumber || !statusLabel || !statusDescription || !sheetEyebrow || !sheetTitle || !sheetDescription || !sheetProjects) {
  throw new Error('The 2.5D portfolio structure is incomplete.');
}

const setActiveRoom = (roomId: RoomId | null): void => {
  shell.dataset.activeRoom = roomId ?? '';
  for (const button of floorMap.querySelectorAll<HTMLButtonElement>('[data-room]')) {
    button.classList.toggle('is-active', button.dataset.room === roomId);
  }

  if (!roomId) {
    statusNumber.textContent = '—';
    statusLabel.textContent = 'Explore the house';
    statusDescription.textContent = 'Move over a floor';
    return;
  }

  const room = ROOMS[roomId];
  statusNumber.textContent = String(6 - FLOOR_ORDER.indexOf(roomId)).padStart(2, '0');
  statusLabel.textContent = room.label;
  statusDescription.textContent = room.description;
};

const openRoom = (roomId: RoomId): void => {
  const room = ROOMS[roomId];
  setActiveRoom(roomId);
  sheet.style.setProperty('--room-accent', room.accent);
  sheetEyebrow.textContent = room.contentKey.replaceAll('-', ' ');
  sheetTitle.textContent = room.label;
  sheetDescription.textContent = room.description;

  if (room.projects.length === 0) {
    sheetProjects.innerHTML = '<p class="room-sheet__empty">This room is ready for future work.</p>';
  } else {
    sheetProjects.replaceChildren(...room.projects.map((project) => {
      const article = document.createElement('article');
      article.className = 'sheet-project';
      article.innerHTML = `
        <img src="${project.image}" alt="${project.imageAlt}" />
        <div>
          <span>${project.category} · ${project.year}</span>
          <h2>${project.title}</h2>
          <p>${project.summary}</p>
        </div>
      `;
      return article;
    }));
  }

  sheet.inert = false;
  sheet.setAttribute('aria-hidden', 'false');
  sheet.classList.add('is-open');
  sheet.querySelector<HTMLButtonElement>('[data-close-room]')?.focus();
};

const closeRoom = (): void => {
  sheet.classList.remove('is-open');
  sheet.setAttribute('aria-hidden', 'true');
  sheet.inert = true;
  setActiveRoom(null);
};

for (const [index, roomId] of FLOOR_ORDER.entries()) {
  const room = ROOMS[roomId];
  const region = FLOOR_REGIONS[roomId];
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'floor-hit';
  button.dataset.room = roomId;
  button.style.setProperty('--floor-top', `${region.top}%`);
  button.style.setProperty('--floor-height', `${region.height}%`);
  button.style.setProperty('--floor-light', room.lightColor);
  button.setAttribute('aria-label', `${room.label}: ${room.description}`);
  button.innerHTML = `<span>${String(6 - index).padStart(2, '0')}</span><strong>${room.label}</strong>`;
  button.addEventListener('pointerenter', () => setActiveRoom(roomId));
  button.addEventListener('pointerleave', () => setActiveRoom(null));
  button.addEventListener('focus', () => setActiveRoom(roomId));
  button.addEventListener('blur', () => {
    if (!sheet.classList.contains('is-open')) setActiveRoom(null);
  });
  button.addEventListener('click', () => openRoom(roomId));
  floorMap.append(button);
}

for (const closeButton of sheet.querySelectorAll<HTMLButtonElement>('[data-close-room]')) {
  closeButton.addEventListener('click', closeRoom);
}

document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && sheet.classList.contains('is-open')) closeRoom();
});

shell.addEventListener('pointermove', (event) => {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const bounds = shell.getBoundingClientRect();
  const x = ((event.clientX - bounds.left) / bounds.width - 0.5) * 2;
  const y = ((event.clientY - bounds.top) / bounds.height - 0.5) * 2;
  shell.style.setProperty('--parallax-x', `${x * 3.5}px`);
  shell.style.setProperty('--parallax-y', `${y * 2.5}px`);
});

shell.addEventListener('pointerleave', () => {
  shell.style.setProperty('--parallax-x', '0px');
  shell.style.setProperty('--parallax-y', '0px');
  if (!sheet.classList.contains('is-open')) setActiveRoom(null);
});

setActiveRoom(null);
