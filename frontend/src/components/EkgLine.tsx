/** Signature motif: an animated ECG trace used across headers, loaders, and the logo mark. */
export default function EkgLine({ className = "", width = 340, height = 60 }) {
  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      width={width}
      height={height}
      className={className}
      aria-hidden="true"
    >
      <path
        className="ekg-line"
        d={`M0 ${height / 2}
            L${width * 0.25} ${height / 2}
            L${width * 0.3} ${height * 0.15}
            L${width * 0.36} ${height * 0.9}
            L${width * 0.42} ${height * 0.5}
            L${width * 0.5} ${height / 2}
            L${width * 0.68} ${height / 2}
            L${width * 0.74} ${height * 0.2}
            L${width * 0.8} ${height * 0.85}
            L${width * 0.86} ${height / 2}
            L${width} ${height / 2}`}
      />
    </svg>
  );
}
