export interface AppLink {
  name: string;
  href: string;
  description: string;
  tag?: string;
}

// Add an entry here and it shows up on the landing page.
export const APPS: AppLink[] = [
  {
    name: 'Avalon Notes Helper',
    href: '/anh3/',
    description: 'Track roles, quests, and votes while playing Avalon in person.',
    tag: '3.0',
  },
];
