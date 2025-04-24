    // Function to handle image upload and display the result
    async function uploadImage(event) {
        event.preventDefault();
        const formData = new FormData();
        const fileInput = document.getElementById("image-file");
        formData.append("image", fileInput.files[0]);

        try {
            const response = await fetch("http://localhost:8000/upload-image", {
                method: "POST",
                body: formData
            });
            const result = await response.json();
            document.getElementById("summary").innerText = result.summary;
            document.getElementById("image-filename").value = result.filename; // Set filename for questions
        } catch (error) {
            console.error("Error uploading image:", error);
        }
    }

    // Function to ask a question about the uploaded image
    async function askQuestion(event) {
        event.preventDefault();
        const filename = document.getElementById("image-filename").value;
        const question = document.getElementById("question-input").value;

        if (!filename || !question) {
            alert("Please upload an image and enter a question.");
            return;
        }

        const response = await fetch(`http://localhost:8000/ask-image/${filename}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ question })
        });
        const result = await response.json();
        document.getElementById("answer").innerText = result.answer;
    }