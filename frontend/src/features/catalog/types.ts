export type CatalogStation = {
  id: number;
  code: string;
  name: string;
  display_order: number | null;
};

export type CatalogSeatType = {
  code: string;
  name: string;
};

export type RailCatalog = {
  stations: CatalogStation[];
  seat_types: CatalogSeatType[];
  service_date_min: string | null;
  service_date_max: string | null;
};
