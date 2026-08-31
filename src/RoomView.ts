import { ROOMS, type ProjectDefinition, type RoomId } from './rooms';

export class RoomView {
  private currentRoom: RoomId | null = null;
  private currentProject: ProjectDefinition | null = null;
  private savedRoomScroll = 0;
  private navigating = false;
  private readonly backButton: HTMLButtonElement;
  private readonly backToProjectsButton: HTMLButtonElement;
  private readonly nextProjectButton: HTMLButtonElement;
  private readonly roomPage: HTMLElement;
  private readonly caseStudy: HTMLElement;
  private readonly projectGrid: HTMLElement;

  constructor(
    private readonly element: HTMLElement,
    onBack: () => void,
  ) {
    const backButton = element.querySelector<HTMLButtonElement>('[data-back-to-house]');
    const backToProjectsButton = element.querySelector<HTMLButtonElement>('[data-back-to-projects]');
    const nextProjectButton = element.querySelector<HTMLButtonElement>('[data-next-project]');
    const roomPage = element.querySelector<HTMLElement>('.room-page');
    const caseStudy = element.querySelector<HTMLElement>('[data-case-study]');
    const projectGrid = element.querySelector<HTMLElement>('[data-project-grid]');

    if (!backButton || !backToProjectsButton || !nextProjectButton || !roomPage || !caseStudy || !projectGrid) {
      throw new Error('The room view is missing required navigation elements.');
    }

    this.backButton = backButton;
    this.backToProjectsButton = backToProjectsButton;
    this.nextProjectButton = nextProjectButton;
    this.roomPage = roomPage;
    this.caseStudy = caseStudy;
    this.projectGrid = projectGrid;

    this.backButton.addEventListener('click', onBack);
    this.backToProjectsButton.addEventListener('click', () => void this.showProjects());
    this.nextProjectButton.addEventListener('click', () => void this.showNextProject());
    this.projectGrid.addEventListener('click', this.onProjectClick);
    document.addEventListener('keydown', this.onKeyDown);
  }

  show(roomId: RoomId): void {
    this.currentRoom = roomId;
    this.currentProject = null;
    this.render(roomId);
    this.roomPage.hidden = false;
    this.caseStudy.hidden = true;
    this.element.scrollTop = 0;
    this.element.hidden = false;
    this.element.setAttribute('aria-hidden', 'false');
  }

  hide(): void {
    this.element.hidden = true;
    this.element.setAttribute('aria-hidden', 'true');
  }

  focusBackButton(): void {
    this.backButton.focus({ preventScroll: true });
  }

  getCurrentRoom(): RoomId | null {
    return this.currentRoom;
  }

  private readonly onProjectClick = (event: MouseEvent): void => {
    const target = event.target;
    if (!(target instanceof Element)) return;
    const link = target.closest<HTMLAnchorElement>('[data-project-slug]');
    if (!link) return;

    event.preventDefault();
    const project = this.findProject(link.dataset.projectSlug);
    if (project) void this.showProject(project);
  };

  private readonly onKeyDown = (event: KeyboardEvent): void => {
    if (event.key !== 'Escape' || !this.currentProject || this.element.hidden) return;
    event.preventDefault();
    void this.showProjects();
  };

  private render(roomId: RoomId): void {
    const room = ROOMS[roomId];
    this.element.style.setProperty('--room-accent', room.accent);
    this.element.dataset.room = roomId;

    const title = this.element.querySelector<HTMLElement>('[data-room-title]');
    const description = this.element.querySelector<HTMLElement>('[data-room-description]');
    const category = this.element.querySelector<HTMLElement>('[data-room-category]');
    const count = this.element.querySelector<HTMLElement>('[data-project-count]');
    const empty = this.element.querySelector<HTMLElement>('[data-project-empty]');

    if (!title || !description || !category || !count || !empty) {
      throw new Error('The room view is missing required content elements.');
    }

    title.textContent = room.label;
    description.textContent = room.description;
    category.textContent = room.contentKey.replaceAll('-', ' ');
    count.textContent = `${room.projects.length} ${room.projects.length === 1 ? 'project' : 'projects'}`;
    document.title = `${room.label} Projects — Filippa Karlsson`;

    const backLabel = this.caseStudy.querySelector<HTMLElement>('[data-back-to-projects-label]');
    const nextLabel = this.caseStudy.querySelector<HTMLElement>('[data-next-project-label]');
    if (backLabel) backLabel.textContent = `${room.label} projects`;
    if (nextLabel) nextLabel.textContent = `Next ${room.label} project`;

    this.projectGrid.replaceChildren(...room.projects.map((project) => this.createProjectCard(project)));
    this.projectGrid.hidden = room.projects.length === 0;
    empty.hidden = room.projects.length > 0;
  }

  private createProjectCard(project: ProjectDefinition): HTMLElement {
    const article = document.createElement('article');
    article.className = 'project-card';
    article.innerHTML = `
      <a class="project-card__link" href="#project-${encodeURIComponent(project.slug)}" data-project-slug="${this.escape(project.slug)}">
        <span class="project-card__media${project.imageFit === 'contain' ? ' is-contained' : ''}">
          <img src="${this.escape(project.image)}" alt="${this.escape(project.imageAlt)}" loading="lazy" />
          <span class="project-card__overlay">
            <span>${this.escape(project.category)}</span>
            <strong>${this.escape(project.title)}</strong>
            <p>${this.escape(project.summary)}</p>
            <em>View case study&nbsp; →</em>
          </span>
        </span>
        <span class="project-card__meta">
          <span>${this.escape(project.category)} · ${this.escape(project.year)}</span>
          <strong>${this.escape(project.title)}</strong>
        </span>
      </a>
    `;
    return article;
  }

  private async showProject(project: ProjectDefinition): Promise<void> {
    if (this.navigating || !this.currentRoom) return;
    this.navigating = true;
    this.savedRoomScroll = this.element.scrollTop;

    try {
      await this.fade(this.roomPage, 1, 0, 220);
      this.currentProject = project;
      this.renderCaseStudy(project);
      this.roomPage.hidden = true;
      this.caseStudy.hidden = false;
      this.element.scrollTop = 0;
      await this.fade(this.caseStudy, 0, 1, 460, 12);
      this.backToProjectsButton.focus({ preventScroll: true });
    } finally {
      this.navigating = false;
    }
  }

  private async showProjects(): Promise<void> {
    if (this.navigating || !this.currentRoom || !this.currentProject) return;
    this.navigating = true;
    const previousSlug = this.currentProject.slug;

    try {
      await this.fade(this.caseStudy, 1, 0, 220);
      this.currentProject = null;
      this.caseStudy.hidden = true;
      this.roomPage.hidden = false;
      this.element.scrollTop = this.savedRoomScroll;
      await this.fade(this.roomPage, 0, 1, 360, 8);
      this.projectGrid
        .querySelector<HTMLAnchorElement>(`[data-project-slug="${CSS.escape(previousSlug)}"]`)
        ?.focus({ preventScroll: true });
      document.title = `${ROOMS[this.currentRoom].label} Projects — Filippa Karlsson`;
    } finally {
      this.navigating = false;
    }
  }

  private async showNextProject(): Promise<void> {
    if (!this.currentRoom || !this.currentProject || this.navigating) return;
    const projects = ROOMS[this.currentRoom].projects;
    const index = projects.findIndex((project) => project.slug === this.currentProject?.slug);
    const next = projects[(index + 1) % projects.length];
    if (!next) return;

    this.navigating = true;
    try {
      await this.fade(this.caseStudy, 1, 0, 220);
      this.currentProject = next;
      this.renderCaseStudy(next);
      this.element.scrollTop = 0;
      await this.fade(this.caseStudy, 0, 1, 420, 10);
    } finally {
      this.navigating = false;
    }
  }

  private renderCaseStudy(project: ProjectDefinition): void {
    const values: Array<[string, string]> = [
      ['[data-case-study-eyebrow]', `${project.category} · ${project.year}`],
      ['[data-case-study-title]', project.title],
      ['[data-case-study-summary]', project.summary],
      ['[data-case-study-category]', project.category],
      ['[data-case-study-deliverable]', project.deliverable],
      ['[data-case-study-year]', project.year],
      ['[data-case-study-purpose]', project.purpose],
      ['[data-case-study-audience]', project.audience],
      ['[data-case-study-approach]', project.approach],
      ['[data-case-study-outcome]', project.outcome],
    ];

    for (const [selector, value] of values) {
      const node = this.caseStudy.querySelector<HTMLElement>(selector);
      if (node) node.textContent = value;
    }

    const image = this.caseStudy.querySelector<HTMLImageElement>('[data-case-study-image]');
    const visual = this.caseStudy.querySelector<HTMLElement>('[data-case-study-visual]');
    const documentLink = this.caseStudy.querySelector<HTMLAnchorElement>('[data-case-study-document]');
    if (!image || !visual || !documentLink) throw new Error('The case study media elements are unavailable.');

    image.src = project.image;
    image.alt = project.imageAlt;
    visual.classList.toggle('is-contained', project.imageFit === 'contain');

    documentLink.hidden = !project.document;
    if (project.document) documentLink.href = project.document;
    else documentLink.removeAttribute('href');

    const projects = this.currentRoom ? ROOMS[this.currentRoom].projects : [];
    const index = projects.findIndex((candidate) => candidate.slug === project.slug);
    const next = projects[(index + 1) % projects.length];
    this.nextProjectButton.hidden = projects.length < 2;
    const nextTitle = this.caseStudy.querySelector<HTMLElement>('[data-next-project-title]');
    if (nextTitle) nextTitle.textContent = next?.title ?? '';

    this.caseStudy.dataset.project = project.slug;
    document.title = `${project.title} — Filippa Karlsson`;
  }

  private findProject(slug: string | undefined): ProjectDefinition | null {
    if (!slug || !this.currentRoom) return null;
    return ROOMS[this.currentRoom].projects.find((project) => project.slug === slug) ?? null;
  }

  private async fade(
    element: HTMLElement,
    from: number,
    to: number,
    duration: number,
    translate = 0,
  ): Promise<void> {
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const animation = element.animate(
      [
        { opacity: from, transform: `translateY(${from === 0 ? translate : 0}px)` },
        { opacity: to, transform: `translateY(${to === 0 ? -translate : 0}px)` },
      ],
      {
        duration: reducedMotion ? 1 : duration,
        easing: 'cubic-bezier(0.22, 1, 0.36, 1)',
        fill: 'forwards',
      },
    );
    await animation.finished;
  }

  private escape(value: string): string {
    const element = document.createElement('span');
    element.textContent = value;
    return element.innerHTML;
  }
}
