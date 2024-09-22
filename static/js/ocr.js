let boundingBoxes = []; // To store bounding boxes
        let uploadedImageUrl = ''; // To store uploaded image URL
        let tooltip = null;

        async function handleFirstButtonClick(event) {
            const file = event.target.files[0];
            if (file) {
                const formData = new FormData();
                formData.append('upload_file_1', file);

                // Show loading overlay
                document.getElementById('loadingOverlay').style.display = 'flex';

                // Send the file to the server
                const response = await fetch("/api/extracttext", {
                    method: "POST",
                    body: formData,
                });

                const result = await response.json();
                document.getElementById('loadingOverlay').style.display = 'none';

                uploadedImageUrl = result.image_url;
                boundingBoxes = result.bounding_boxes; // Store bounding boxes

                // Reset images
                const uploadedImageElement = document.getElementById('uploadedImage');
                const canvas = document.getElementById('imageCanvas');
                const ctx = canvas.getContext('2d');

                // Clear previous image and canvas
                uploadedImageElement.src = '';
                uploadedImageElement.style.display = 'none';
                canvas.style.display = 'none';

                if (uploadedImageUrl && boundingBoxes.length > 0) {
                    // Show the uploaded image
                    uploadedImageElement.src = uploadedImageUrl;
                    uploadedImageElement.style.display = 'block';

                    // Load the uploaded image into the canvas
                    const uploadedImage = new Image();
                    uploadedImage.src = uploadedImageUrl;
                    uploadedImage.onload = function () {
                        // Set canvas size to the image size
                        canvas.width = uploadedImage.width;
                        canvas.height = uploadedImage.height;

                        // Draw the image on the canvas
                        ctx.drawImage(uploadedImage, 0, 0);
                        drawBoundingBoxes(ctx, boundingBoxes);

                        // Show the canvas
                        canvas.style.display = 'block';
                    };

                    // Initialize tooltip
                    tooltip = document.createElement('div');
                    tooltip.className = 'tooltip';
                    document.body.appendChild(tooltip);

                    // Add mouse event listeners for hover effect
                    canvas.addEventListener('mousemove', (e) => showTextOnHover(e, canvas, boundingBoxes, uploadedImage));
                    canvas.addEventListener('mouseout', () => hideTooltip());
                }
            }
        }

        function drawBoundingBoxes(ctx, boxes) {
            boxes.forEach(box => {
                ctx.strokeStyle = 'red';
                ctx.lineWidth = 2;
                ctx.strokeRect(box.x, box.y, box.width, box.height);
            });
        }

        function showTextOnHover(event, canvas, boxes, uploadedImage) {
            const rect = canvas.getBoundingClientRect();
            const mouseX = event.clientX - rect.left;
            const mouseY = event.clientY - rect.top;

            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height); // Clear canvas before redrawing

            // Redraw the original image
            ctx.drawImage(uploadedImage, 0, 0);
            drawBoundingBoxes(ctx, boxes); // Redraw bounding boxes

            let found = false;

            boxes.forEach(box => {
                // Check if mouse is within the bounding box
                if (mouseX >= box.x && mouseX <= box.x + box.width &&
                    mouseY >= box.y && mouseY <= box.y + box.height) {
                    tooltip.style.left = `${event.pageX + 10}px`;
                    tooltip.style.top = `${event.pageY + 10}px`;
                    tooltip.innerText = box.text;
                    tooltip.style.display = 'block'; // Show tooltip
                    found = true;
                }
            });

            if (!found) {
                hideTooltip(); // Hide tooltip if not hovering over a box
            }
        }

        function hideTooltip() {
            if (tooltip) {
                tooltip.style.display = 'none'; // Hide tooltip
            }
        }