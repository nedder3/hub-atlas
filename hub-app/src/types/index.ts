export interface Participant {
  id: string;
  name: string;
  avatar: string;
  color: string;
  role: string;
  online: boolean;
}

export interface HubConfig {
  hub_path: string;
  participants: Participant[];
}

export interface Message {
  id: string;
  date: string;
  author: string;
  role: string;
  content: string;
  file_path: string;
  parent?: string;
  project?: string;
}
