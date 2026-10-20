-- ============================================
-- Migración 011: Evitar reservas superpuestas a nivel de base de datos
-- ============================================
-- Un profesional no puede tener dos reservas activas (confirmed/rescheduled)
-- con rangos horarios que se superponen. Cierra la condición de carrera entre
-- la validación de conflictos y el INSERT.
--
-- Si ya existen reservas superpuestas, la restricción no se crea y se emite un
-- WARNING (para no impedir el arranque de la app). Corregir esos datos y crearla a mano.

CREATE EXTENSION IF NOT EXISTS btree_gist;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'bookings_no_overlap'
    ) THEN
        RETURN;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM bookings a
        JOIN bookings b
          ON a.professional_id = b.professional_id
         AND a.id < b.id
         AND a.status IN ('confirmed', 'rescheduled')
         AND b.status IN ('confirmed', 'rescheduled')
         AND tstzrange(a.starts_at, a.ends_at) && tstzrange(b.starts_at, b.ends_at)
    ) THEN
        RAISE WARNING 'bookings_no_overlap no creada: existen reservas superpuestas';
        RETURN;
    END IF;

    ALTER TABLE bookings
        ADD CONSTRAINT bookings_no_overlap
        EXCLUDE USING gist (
            professional_id WITH =,
            tstzrange(starts_at, ends_at) WITH &&
        )
        WHERE (status IN ('confirmed', 'rescheduled'));
END
$$;
