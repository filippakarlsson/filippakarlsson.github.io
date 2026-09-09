import './two-d.css';

type Floor = {
  name: string;
  top: number;
  height: number;
  lampX: number;
  lampY: number;
  color: string;
};

const FLOORS: readonly Floor[] = [
  { name: 'Rooftop', top: 2.4, height: 20.7, lampX: 51.0, lampY: 34.6, color: '#ffd69a' },
  { name: 'Studio', top: 25.0, height: 12.3, lampX: 51.0, lampY: 19.5, color: '#ffcf82' },
  { name: 'Office', top: 38.7, height: 12.9, lampX: 50.8, lampY: 24.0, color: '#ffc56e' },
  { name: 'Playroom', top: 52.0, height: 13.6, lampX: 51.0, lampY: 27.4, color: '#ffb776' },
  { name: 'Welcome', top: 66.0, height: 13.5, lampX: 50.9, lampY: 24.7, color: '#ffd09a' },
  { name: 'Basement', top: 80.2, height: 15.2, lampX: 50.9, lampY: 25.3, color: '#ffc06c' },
];

const floorMap = document.querySelector<HTMLElement>('[data-floor-map]');

if (!floorMap) throw new Error('The house floor map is missing.');

for (const floor of FLOORS) {
  const region = document.createElement('div');
  region.className = 'floor';
  region.tabIndex = 0;
  region.setAttribute('role', 'group');
  region.setAttribute('aria-label', `${floor.name} floor. Focus or hover to switch on its lamp.`);
  region.style.setProperty('--floor-top', `${floor.top}%`);
  region.style.setProperty('--floor-height', `${floor.height}%`);
  region.style.setProperty('--lamp-x', `${floor.lampX}%`);
  region.style.setProperty('--lamp-y', `${floor.lampY}%`);
  region.style.setProperty('--lamp-color', floor.color);
  floorMap.append(region);
}
