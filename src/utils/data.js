export const KG_TO_LB = 2.20462

function normalizeName(name) {
  if (!name) return ''
  return String(name).trim().toLowerCase().replace(/[^a-z0-9\s]/g, '').replace(/\s+/g, ' ')
}

function parseDate(d) {
  if (!d) return null
  const t = new Date(d)
  return isNaN(t.getTime()) ? null : t.toISOString().slice(0,10)
}

function toNumber(v) {
  if (v === undefined || v === null) return null
  const n = Number(String(v).replace(/[^0-9\.\-]/g, ''))
  return isNaN(n) ? null : n
}

export function processCsvData(rows) {
  // rows is array of objects from PapaParse header=true
  return rows.map(r => {
    const out = {}
    // prefer common column names if present
    out.Name = r.Name || r.name || r.lifter || ''
    out.NameNormalized = normalizeName(out.Name)
    out.MeetDate = parseDate(r.MeetDate || r.meet_date || r.date || r.meetdate) || null
    out.Equipment = r.Equipment || r.equipment || r.Gear || ''
    out.Federation = r.Federation || r.federation || ''
    out.Age = toNumber(r.Age || r.age)
    out.BodyweightKg = toNumber(r.BodyweightKg || r.bodyweight || r.bodywt || r.weight)

    out.SquatKg = toNumber(r.SquatKg || r.squat || r.best3sqkg || r.best3sq)
    out.BenchKg = toNumber(r.BenchKg || r.bench || r.best3bnkg || r.best3bn)
    out.DeadliftKg = toNumber(r.DeadliftKg || r.deadlift || r.best3dlkg || r.best3dl)
    out.TotalKg = toNumber(r.TotalKg || r.total || r.totalkg)

    out.SquatLb = out.SquatKg != null ? +(out.SquatKg * KG_TO_LB).toFixed(2) : null
    out.BenchLb = out.BenchKg != null ? +(out.BenchKg * KG_TO_LB).toFixed(2) : null
    out.DeadliftLb = out.DeadliftKg != null ? +(out.DeadliftKg * KG_TO_LB).toFixed(2) : null
    out.TotalLb = out.TotalKg != null ? +(out.TotalKg * KG_TO_LB).toFixed(2) : null

    return out
  })
}

export { normalizeName }
