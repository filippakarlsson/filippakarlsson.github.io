export const ROOM_IDS = [
  'basement',
  'welcome',
  'playroom',
  'office',
  'studio',
  'rooftop',
] as const;

export type RoomId = (typeof ROOM_IDS)[number];

export interface ProjectDefinition {
  title: string;
  category: string;
  image: string;
  imageAlt: string;
  year: string;
  slug: string;
  summary: string;
  deliverable: string;
  purpose: string;
  audience: string;
  approach: string;
  outcome: string;
  imageFit?: 'cover' | 'contain';
  document?: string;
}

export interface RoomDefinition {
  id: RoomId;
  label: string;
  contentKey: string;
  description: string;
  lightColor: string;
  accent: string;
  projects: ProjectDefinition[];
}

export const ROOMS: Record<RoomId, RoomDefinition> = {
  basement: {
    id: 'basement',
    label: 'Basement',
    contentKey: 'experiments',
    description: 'Experiments, prototypes and lessons learned',
    lightColor: '#ff9a45',
    accent: '#dfb79f',
    projects: [],
  },
  welcome: {
    id: 'welcome',
    label: 'Welcome',
    contentKey: 'introduction',
    description: 'Introduction and selected perspective',
    lightColor: '#ffb267',
    accent: '#e8c99f',
    projects: [],
  },
  playroom: {
    id: 'playroom',
    label: 'Playroom',
    contentKey: 'creative-code',
    description: 'Creative coding and experimental digital work',
    lightColor: '#ff8f50',
    accent: '#e5b1a4',
    projects: [],
  },
  office: {
    id: 'office',
    label: 'Office',
    contentKey: 'digital-design',
    description: 'UX, UI and digital interfaces',
    lightColor: '#ffad5d',
    accent: '#aec9c2',
    projects: [
      {
        title: 'TrendBot',
        category: 'UX/UI design',
        image: '/projects/office/trendbot-landing-page.png',
        imageAlt: 'TrendBot landing page with a large Swedish headline, feature panel and orange call-to-action',
        year: '2026',
        slug: 'trendbot',
        summary: 'A conversion-focused landing page that makes real-time trend intelligence feel clear, immediate and easy to act on.',
        deliverable: 'Responsive web experience',
        purpose: 'Present TrendBot as a practical way to discover fast-growing topics before they peak, while guiding visitors towards trying the product or choosing a plan.',
        audience: 'Social media managers, content teams and marketers who need to decide what to publish while interest is still growing.',
        approach: 'The experience leads with one direct promise and a strong call to action. Oversized type creates urgency, while a structured product panel explains the most useful signals in plain language. Warm neutrals, vivid orange actions and a deep green supporting card give the page a confident but approachable product identity.',
        outcome: 'A focused responsive landing-page concept with clear product positioning, scannable benefits and an obvious path from first impression to sign-up.',
      },
      {
        title: 'TripFlow',
        category: 'UX/UI design',
        image: '/projects/office/tripflow-landing-page.png',
        imageAlt: 'TripFlow travel-planning landing page with hot-air balloons, a photographer and prominent sign-up actions',
        year: '2026',
        slug: 'tripflow',
        summary: 'A cinematic travel-planning landing page that turns a complex planning task into an inviting and focused first step.',
        deliverable: 'Responsive landing page',
        purpose: 'Introduce TripFlow as one organised place for planning memorable trips, while giving new and returning users clear paths into the product.',
        audience: 'Independent travellers who want inspiration and a simpler way to organise the practical parts of a journey.',
        approach: 'The interface opens with a full-screen destination photograph and a strong two-line promise. A cool blue call to action establishes the primary route, while repeated log-in access supports returning users without competing with sign-up. High-contrast typography and generous spacing keep the message readable over the image.',
        outcome: 'A focused landing-page concept with a clear hierarchy, recognisable travel atmosphere and an immediate path from inspiration to account creation.',
      },
    ],
  },
  studio: {
    id: 'studio',
    label: 'Studio',
    contentKey: 'visual-design',
    description: 'Branding, typography and visual design',
    lightColor: '#ffb774',
    accent: '#c8b8d3',
    projects: [
      {
        title: 'CRAZ Issue 02',
        category: 'Editorial design',
        image: '/projects/studio/craz-editorial.jpg',
        imageAlt: 'Open CRAZ fashion magazine and cover mockup in black and white',
        year: '2026',
        slug: 'craz-issue-02',
        summary: 'A fashion editorial concept built around expressive typography, monochrome photography and a calm magazine grid.',
        deliverable: 'Magazine concept',
        purpose: 'Explore how a contemporary fashion publication can balance image-led storytelling with comfortable long-form reading.',
        audience: 'Readers interested in fashion, visual culture and independent editorial design.',
        approach: 'A restrained black-and-white palette lets the photography lead. Oversized display lettering creates a recognisable voice, while a measured column grid keeps the interior pages clear and consistent.',
        outcome: 'A cohesive editorial direction shown across a cover and multi-page spread, with a visual system that can expand to future issues.',
      },
      {
        title: 'Infoservice Exhibition',
        category: 'Spatial branding',
        image: '/projects/studio/infoservice-exhibition.jpg',
        imageAlt: 'Blue Infoservice exhibition stand with wall graphics, counter, seating and flag',
        year: '2026',
        slug: 'infoservice-exhibition',
        summary: 'A modular exhibition environment translating Infoservice’s print and signage offer into one coherent branded space.',
        deliverable: 'Exhibition concept',
        purpose: 'Make Infoservice’s range of print, signage and communication services immediately understandable in a busy exhibition setting.',
        audience: 'Trade-show visitors and organisations looking for practical print, display and profiling services.',
        approach: 'The existing deep-blue identity is extended across large wall graphics, a service panel, reception counter and flag. Product photography demonstrates the offer while the central message stays readable from a distance.',
        outcome: 'A complete stand concept with a consistent visual language across large-format graphics, furniture and branded touchpoints.',
      },
      {
        title: 'Arla Charge',
        category: 'Packaging design',
        image: '/projects/studio/arla-charge-packaging.jpg',
        imageAlt: 'Three black Arla Charge milk cartons in green, orange and pink flavours',
        year: '2026',
        slug: 'arla-charge',
        summary: 'A high-energy packaging concept for a flavoured milk range built as a bold three-product family.',
        deliverable: 'Packaging concept',
        purpose: 'Give a protein, calcium and energy-focused milk range a distinctive shelf presence while keeping the flavour variants easy to recognise.',
        audience: 'Active, on-the-go consumers looking for a filling milk drink with a more energetic visual identity.',
        approach: 'A black carton creates a shared base for the range. Electric diagonal graphics, condensed typography and colour-coded caps separate natural, chocolate and strawberry variants without losing family consistency.',
        outcome: 'A three-flavour packaging system with clear variant recognition and a strong, unified silhouette at shelf distance.',
      },
      {
        title: 'Tekniska Högskolan',
        category: 'Catalogue design',
        image: '/projects/studio/jth-catalogue-cover.png',
        imageAlt: 'Purple, orange and grey programme catalogue cover for Tekniska Högskolan',
        year: '2027 / 2028',
        slug: 'tekniska-hogskolan-catalogue',
        summary: 'A programme catalogue cover for Tekniska Högskolan at Jönköping University, connecting technical subjects through one graphic system.',
        deliverable: 'Education catalogue cover',
        purpose: 'Introduce the 2027/2028 programme catalogue with a clear, contemporary expression that makes technical education feel connected and forward-looking.',
        audience: 'Prospective students comparing engineering and technical programmes at Jönköping University.',
        approach: 'Circuit-like lines guide the eye through icons for computing, science and engineering. Purple establishes the school identity, while orange highlights add energy and hierarchy against white and grey fields.',
        outcome: 'A single cover direction that brings several technical disciplines together while keeping the school, year and catalogue purpose immediately legible.',
        imageFit: 'contain',
        document: '/projects/studio/jth-catalogue.pdf',
      },
    ],
  },
  rooftop: {
    id: 'rooftop',
    label: 'Rooftop',
    contentKey: 'contact',
    description: 'Current work, about and contact',
    lightColor: '#ffd19a',
    accent: '#d9c8a5',
    projects: [],
  },
};

export function isRoomId(value: unknown): value is RoomId {
  return typeof value === 'string' && ROOM_IDS.includes(value as RoomId);
}
