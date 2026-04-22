"use client";

import React, { useState } from "react";
import { Plus, MapPin, Phone, Edit2, Trash2, ChevronDown, ChevronUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Location } from "@/lib/types";
import { cn } from "@/lib/utils";

interface LocationListProps {
  locations?: Location[];
  loading?: boolean;
  onAdd?: () => void;
  onEdit?: (location: Location) => void;
  onDelete?: (location: Location) => void;
  onSelect?: (location: Location) => void;
}

export function LocationList({
  locations = [],
  loading = false,
  onAdd,
  onEdit,
  onDelete,
  onSelect,
}: LocationListProps) {
  const [search, setSearch] = useState("");
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const filtered = locations.filter((loc) =>
    loc.name.toLowerCase().includes(search.toLowerCase()) ||
    loc.city.toLowerCase().includes(search.toLowerCase()) ||
    loc.address.toLowerCase().includes(search.toLowerCase())
  );

  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-20 rounded-lg" />
        ))}
      </div>
    );
  }

  const formatAddress = (loc: Location) => {
    return `${loc.address}, ${loc.city}, ${loc.state} ${loc.postal_code || ""}`.trim();
  };

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <Input
          placeholder="Search locations..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1"
        />
        <Button onClick={onAdd} className="gap-2">
          <Plus className="h-4 w-4" />
          Add Location
        </Button>
      </div>

      <div className="space-y-2">
        {filtered.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            {locations.length === 0 ? "No locations yet" : "No matching locations"}
          </div>
        ) : (
          filtered.map((location) => (
            <div
              key={location.id}
              className="border rounded-lg p-4 hover:bg-accent/50 cursor-pointer transition"
              onClick={() => {
                setExpandedId(expandedId === location.id ? null : location.id);
                onSelect?.(location);
              }}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="font-semibold">{location.name}</h3>
                  <div className="text-sm text-muted-foreground space-y-1 mt-1">
                    <div className="flex items-center gap-2">
                      <MapPin className="h-4 w-4" />
                      {formatAddress(location)}
                    </div>
                    {location.phone && (
                      <div className="flex items-center gap-2">
                        <Phone className="h-4 w-4" />
                        {location.phone}
                      </div>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {expandedId === location.id ? (
                    <ChevronUp className="h-4 w-4" />
                  ) : (
                    <ChevronDown className="h-4 w-4" />
                  )}
                </div>
              </div>

              {expandedId === location.id && (
                <div className="mt-4 pt-4 border-t space-y-2 flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={(e) => {
                      e.stopPropagation();
                      onEdit?.(location);
                    }}
                    className="gap-2"
                  >
                    <Edit2 className="h-4 w-4" />
                    Edit
                  </Button>
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={(e) => {
                      e.stopPropagation();
                      onDelete?.(location);
                    }}
                    className="gap-2"
                  >
                    <Trash2 className="h-4 w-4" />
                    Delete
                  </Button>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
