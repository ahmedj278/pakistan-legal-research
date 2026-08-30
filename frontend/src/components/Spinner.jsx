// Plain CSS spinner, no dependency — used anywhere a request is in
// flight. `label` is shown next to it since a bare spinner with no
// text is ambiguous about what's loading.
function Spinner({ label }) {
  return (
    <div className="spinner-row" role="status">
      <span className="spinner" aria-hidden="true" />
      {label && <span>{label}</span>}
    </div>
  );
}

export default Spinner;
