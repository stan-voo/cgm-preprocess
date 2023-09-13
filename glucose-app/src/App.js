import React, { useRef, useState, useEffect } from 'react';
import 'bootstrap/dist/css/bootstrap.min.css';
import axios from 'axios';

function App() {
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  
  useEffect(() => {
    document.title = "FreeStyle Libre 3 Data Export Processing";
  }, []);
  
  const fileInput = useRef(null);
  const [link, setLink] = useState(null);

  const handleUpload = async () => {
    setLoading(true); // Start loading animation when upload begins.
    setSuccess(false);
    const formData = new FormData();
    formData.append('file', fileInput.current.files[0]);

    try {
      const response = await axios.post('http://localhost:5000/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      if (response.data.success) {
        setLink('http://localhost:5000/download');
        setSuccess(true); // Show success message when processing is complete.
      }
    } catch (error) {
      console.error("There was an error uploading the file", error);
      setLoading(false); // Stop the loading animation if there's an error.
    } finally {
      setLoading(false); // Ensure loading animation stops after request is complete.
    }
  };

  return (
    <div className="container mt-5">
      <h1 className="mb-5 text-center">FreeStyle Libre 3 Data Export Processing</h1>
      <div className="mb-3">
        <input type="file" ref={fileInput} />
      </div>
      <button className="btn btn-primary" onClick={handleUpload}>Upload and Process</button>
      {loading && <div className="mt-3">Processing...</div>}
      {success && <div className="mt-3">Data processing complete!</div>}
      {link && <div className="mt-3">
        <a href={link} download>Download Processed CSV</a>
      </div>}
    </div>
  );
}

export default App;
