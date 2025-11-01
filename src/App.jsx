import React, { useEffect, useMemo, useState } from 'react'
import Papa from 'papaparse'
import Fuse from 'fuse.js'
import Plot from 'react-plotly.js'

import { normalizeName, KG_TO_LB, processCsvData } from './utils/data'

export default function App() {
  const [rows, setRows] = useState([])
  const [query, setQuery] = useState('')
  const [selected, setSelected] = useState('')
  const [unit, setUnit] = useState('kg')
  const [lifts, setLifts] = useState({ Squat: true, Bench: true, Deadlift: true, Total: false })
  const [equipment, setEquipment] = useState('All')

  useEffect(() => {
    // load sample csv from public folder
    fetch('/data/sample.csv').then(r => r.text()).then(txt => {
      Papa.parse(txt, { header: true, skipEmptyLines: true, complete: (p) => {
        const data = processCsvData(p.data)
        setRows(data)
      }})
    }).catch(err => console.error(err))
  }, [])

  const names = useMemo(() => Array.from(new Set(rows.map(r => r.Name).filter(Boolean))).sort(), [rows])

  const fuse = useMemo(() => new Fuse(names, { includeScore: true, threshold: 0.4 }), [names])
  const matches = useMemo(() => query ? fuse.search(query).map(x => x.item) : [], [fuse, query])

  useEffect(() => {
    if (matches.length > 0) setSelected(matches[0])
  }, [matches])

  const filtered = useMemo(() => {
    if (!selected) return []
    let arr = rows.filter(r => r.Name === selected)
    if (equipment !== 'All') {
      if (equipment === 'Raw') arr = arr.filter(r => (r.Equipment || '').toLowerCase().includes('raw'))
      else arr = arr.filter(r => !((r.Equipment || '').toLowerCase().includes('raw')))
    }
    return arr.sort((a,b) => new Date(a.MeetDate) - new Date(b.MeetDate))
  }, [rows, selected, equipment])

  const traces = useMemo(() => {
    const active = Object.entries(lifts).filter(([k,v]) => v).map(([k]) => k)
    const unitSuffix = unit === 'kg' ? 'Kg' : 'Lb'
    return active.map(lift => ({
      x: filtered.map(r => r.MeetDate),
      y: filtered.map(r => r[ lift + unitSuffix ]),
      type: 'scatter',
      mode: 'lines+markers',
      name: lift
    }))
  }, [filtered, lifts, unit])

  return (
    <div className="container">
      <header>
        <h1>Lifter Progression</h1>
      </header>
      <aside className="sidebar">
        <section>
          <label>Search (fuzzy)</label>
          <input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Type a lifter name" />
          <div className="matches">
            {matches.slice(0,8).map(m => (
              <button key={m} onClick={() => { setSelected(m); setQuery('') }}>{m}</button>
            ))}
          </div>
        </section>

        <section>
          <label>Select from list</label>
          <select value={selected} onChange={e=>setSelected(e.target.value)}>
            <option value="">-- pick --</option>
            {names.map(n => <option key={n} value={n}>{n}</option>)}
          </select>
        </section>

        <section>
          <label>Lifts</label>
          {Object.keys(lifts).map(k => (
            <div key={k}><label><input type="checkbox" checked={lifts[k]} onChange={e => setLifts(s => ({...s, [k]: e.target.checked}))} /> {k}</label></div>
          ))}
        </section>

        <section>
          <label>Units</label>
          <div>
            <label><input type="radio" checked={unit==='kg'} onChange={()=>setUnit('kg')} /> kg</label>
            <label><input type="radio" checked={unit==='lb'} onChange={()=>setUnit('lb')} /> lb</label>
          </div>
        </section>

        <section>
          <label>Equipment</label>
          <select value={equipment} onChange={e=>setEquipment(e.target.value)}>
            <option>All</option>
            <option>Raw</option>
            <option>Equipped</option>
          </select>
        </section>
      </aside>

      <main>
        {!selected ? (
          <p>Select a lifter to see progression.</p>
        ) : (
          <Plot
            data={traces}
            layout={{ title: `${selected} progression`, xaxis: {title: 'Date'}, yaxis: {title: unit} }}
            useResizeHandler
            style={{width: '100%', height: '600px'}}
          />
        )}
      </main>
    </div>
  )
}
