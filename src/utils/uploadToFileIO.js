export async function uploadToFileIO(blob) {
    const formData = new FormData();
    formData.append("file", blob, "audio.webm");
  
    try {
      const response = await fetch("https://file.io", {
        method: "POST",
        body: formData,
      });
  
      const data = await response.json();
      if (data.success && data.link) {
        console.log("✅ Uploaded to file.io:", data.link);
        return data.link;
      } else {
        console.error("❌ file.io upload failed:", data);
        return null;
      }
    } catch (error) {
      console.error("❌ Upload error:", error);
      return null;
    }
  }
  