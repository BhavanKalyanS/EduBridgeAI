import { useEffect, useRef, useState } from "react";
import { GlobalWorkerOptions, getDocument } from "pdfjs-dist";
import pdfWorkerUrl from "pdfjs-dist/build/pdf.worker.min.mjs?url";

GlobalWorkerOptions.workerSrc = pdfWorkerUrl;

export default function TextbookPdfViewer({ file, title }) {
  const containerRef = useRef(null);
  const [attempt, setAttempt] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    let loadingTask;
    const renderTasks = [];

    async function renderPdf() {
      setLoading(true);
      setError("");

      try {
        loadingTask = getDocument({ data: await file.arrayBuffer() });
        const pdf = await loadingTask.promise;
        const container = containerRef.current;
        if (!active || !container) return;

        container.replaceChildren();
        const outputScale = window.devicePixelRatio || 1;

        for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber += 1) {
          if (!active) return;
          const page = await pdf.getPage(pageNumber);
          const baseViewport = page.getViewport({ scale: 1 });
          const scale = Math.min(1.5, (container.clientWidth - 24) / baseViewport.width);
          const viewport = page.getViewport({ scale });
          const canvas = document.createElement("canvas");
          const context = canvas.getContext("2d");
          if (!context) throw new Error("Canvas rendering is unavailable.");

          canvas.className = "textbook-pdf-page";
          canvas.setAttribute("aria-label", `${title}, page ${pageNumber}`);
          canvas.width = Math.floor(viewport.width * outputScale);
          canvas.height = Math.floor(viewport.height * outputScale);
          canvas.style.width = `${Math.floor(viewport.width)}px`;
          canvas.style.height = `${Math.floor(viewport.height)}px`;
          container.append(canvas);

          const task = page.render({
            canvasContext: context,
            viewport,
            transform: outputScale === 1 ? null : [outputScale, 0, 0, outputScale, 0, 0],
          });
          renderTasks.push(task);
          await task.promise;
        }

        if (active) setLoading(false);
      } catch (renderError) {
        if (active) {
          setError(renderError.message || "Unable to render this PDF.");
          setLoading(false);
        }
      }
    }

    renderPdf();
    return () => {
      active = false;
      renderTasks.forEach((task) => task.cancel());
      loadingTask?.destroy();
    };
  }, [attempt, file, title]);

  return (
    <div className="textbook-pdf-viewer">
      {loading && <div className="textbook-pdf-status" role="status">Rendering textbook PDF...</div>}
      {error && (
        <div className="textbook-pdf-status textbook-pdf-error" role="alert">
          <span>Could not render the textbook PDF. {error}</span>
          <button type="button" onClick={() => setAttempt((value) => value + 1)}>Retry rendering</button>
        </div>
      )}
      <div className="textbook-pdf-pages" ref={containerRef} aria-label={`${title} pages`} />
    </div>
  );
}
