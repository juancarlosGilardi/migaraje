"""Catálogo curado de componentes mantenibles con intervalos verificados
(manuales de fábrica y guías de talleres — ver memoria del proyecto).
Fuente única compartida entre la migración de Alembic (producción) y los
tests (que construyen el esquema con Base.metadata, sin correr migraciones).

category: motor | frenos | transmision | direccion_suspension | llantas | electrico
Cada tupla: (name, category, default_interval_km, default_interval_months, notes)
"""

COMPONENTS: list[tuple[str, str, int | None, int | None, str | None]] = [
    ("Aceite y filtro de motor", "motor", 10000, 12, None),
    ("Filtro de aire del motor", "motor", 20000, 24, None),
    ("Filtro de aire de cabina (polen)", "motor", 15000, 12, None),
    ("Bujías", "motor", 60000, None, "Cobre: cada 20,000-30,000 km · Iridio/platino: hasta 60,000-100,000 km"),
    ("Correa o cadena de distribución", "motor", 90000, 60, "Confirma en tu manual si tu motor usa correa (cambio obligatorio) o cadena (solo inspección)"),
    ("Correa de accesorios (alternador/AC)", "motor", 100000, None, None),
    ("Refrigerante / anticongelante", "motor", 40000, 24, None),
    ("Filtro de combustible", "motor", 40000, 24, "Especialmente relevante en motores diésel"),
    ("Líquido de frenos", "frenos", 40000, 24, None),
    ("Pastillas de freno delanteras", "frenos", 40000, 24, None),
    ("Pastillas de freno traseras", "frenos", 50000, 30, None),
    ("Discos de freno", "frenos", 80000, None, "Revisar desgaste; normalmente dura 2 cambios de pastillas"),
    ("Aceite de caja (transmisión)", "transmision", 60000, 48, "Automática o manual según tu auto"),
    ("Aceite de diferencial", "transmision", 40000, 24, "Solo si tu auto es 4x4 o AWD"),
    ("Líquido de dirección hidráulica", "direccion_suspension", 50000, 48, "No aplica si tu auto tiene dirección eléctrica (EPS)"),
    ("Amortiguadores", "direccion_suspension", 80000, None, "Revisión; cambiar si hay fugas o rebote excesivo"),
    ("Rótulas y terminales de dirección", "direccion_suspension", 60000, None, "Revisión de juego y desgaste"),
    ("Rotación de llantas", "llantas", 10000, 6, None),
    ("Alineamiento y balanceo", "llantas", 10000, 6, None),
    ("Cambio de llantas", "llantas", 50000, 60, "Según desgaste real del labrado, no solo el kilometraje"),
    ("Batería", "electrico", None, 36, None),
    ("Plumillas (limpiaparabrisas)", "electrico", None, 12, None),
    ("Revisión de luces", "electrico", None, 12, None),
]
