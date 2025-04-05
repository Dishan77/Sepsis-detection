import React, { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import axios from "axios";
import "./App.css";

function FileUploader({ type }) {
  const [fileName, setFileName] = useState(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [result, setResult] = useState(null);
  const [extractedData, setExtractedData] = useState(null);

  const onDrop = useCallback((acceptedFiles) => {
    const file = acceptedFiles[0];
    if (!file) return;

    const fileExtension = file.name.split(".").pop().toLowerCase();
    const isPDF = type === "pdf" && fileExtension === "pdf";
    const isAudio =
      type === "audio" && ["mp3", "wav", "flac", "ogg", "m4a", "mp4"].includes(fileExtension);

    if (!isPDF && !isAudio) {
      setErrorMsg(`Invalid file type for ${type.toUpperCase()}.`);
      return;
    }

    setFileName(file.name);
    uploadFile(file);
  }, [type]);

  const { getRootProps, getInputProps } = useDropzone({
    onDrop,
    multiple: false,
    noClick: false,
    noKeyboard: false,
  });

  const uploadFile = async (file) => {
    setLoading(true);
    setErrorMsg(null);
    setResult(null);
    setExtractedData(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const endpoint = type === "pdf" ? "upload_pdf" : "upload_audio";
      const res = await axios.post(`http://localhost:5000/${endpoint}`, formData);

      const predictionValue = Array.isArray(res.data.prediction)
        ? res.data.prediction[0]
        : res.data.prediction;

      setResult(predictionValue);
      setExtractedData(res.data.extracted_data);
    } catch (err) {
      setErrorMsg(err.response?.data?.error || "Upload failed.");
    } finally {
      setLoading(false);
    }
  };

  const renderExtractedData = (data) => {
    if (!data || typeof data !== "object") return null;

    return (
      <table className="data-table">
        <tbody>
          {Object.entries(data).map(([key, value]) => (
            <tr key={key}>
              <td><strong>{key}</strong></td>
              <td>{typeof value === "object" ? JSON.stringify(value) : String(value)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    );
  };

  return (
    <div className="upload-box">
      <h2>{type === "pdf" ? "📄 Upload PDF" : "🔊 Upload Audio / MP4"}</h2>
      <div {...getRootProps({ className: "dropzone" })}>
        <input {...getInputProps()} />
        <p>Drag & drop or click to select a {type === "pdf" ? "PDF" : "audio/video"} file</p>
        {fileName && <p className="file-name">Selected: {fileName}</p>}
      </div>

      {loading && (
        <div className="cyberpunk-loader" title={`Processing ${type.toUpperCase()}...`}></div>
      )}

      {errorMsg && <p className="message error">{errorMsg}</p>}

      {result !== null && (
        <div className={`result-box ${result === 1 ? "success" : "failure"}`}>
          <h3>📊 {type.toUpperCase()} Prediction:</h3>
          <p>{result === 1 ? "✅ Sepsis Detected" : "❌ Sepsis Not Detected"}</p>

          {extractedData && (
            <div className="json-box">
              <h4>📋 Extracted Data:</h4>
              {renderExtractedData(extractedData)}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function App() {
  return (
    <>
      <header className="header">
        <h1>🧬 Sepsis Detection</h1>
      </header>
      <div className="container">
        <div className="dropzones">
          <FileUploader type="pdf" />
          <FileUploader type="audio" />
        </div>
      </div>
    </>
  );
}

export default App;
