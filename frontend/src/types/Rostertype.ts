export type RosterPlayer = {
  player_id: number;
  full_name: string;
  position: string | null;
  headshot_url: string | null;
  team: string | null;
  salary: string | number | null;
  predicted_salary: string | number | null;
  verdict: string | null;
};

export type RosterSummary = {
  id: number;
  name: string;
  player_count: number;
  total_salary: string | number;
  total_predicted_salary: string | number;
};

export type RosterOut = RosterSummary & {
  players: RosterPlayer[];
};
