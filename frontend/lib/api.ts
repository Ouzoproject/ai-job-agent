const API_URL = "http://localhost:8000";

export async function sendMessage(
  message: string,
  cvFile?: File,
  history: { role: "user" | "assistant"; content: string }[] = [],
) {
  const formData = new FormData();
  formData.append("message", message);
  formData.append("history", JSON.stringify(history));
  if (cvFile) formData.append("cv", cvFile);

  const response = await fetch(`${API_URL}/search`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Error sending message: ${error}`);
  }

  return response.json();
}
