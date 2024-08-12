document.addEventListener("DOMContentLoaded", function () {
  var fileInput = document.getElementById("fileInput");
  var filePreview = document.getElementById("filePreview");
  var fileNameSpan = document.getElementById("fileName");
  var removeFileButton = document.getElementById("removeFile");
  var uploadArea = document.querySelector(".border-dashed");
  var convertButton = document.getElementById("convertButton");
  var downloadLink = document.getElementById("downloadLink");

  if (fileInput) {
    fileInput.addEventListener("change", function (event) {
      var files = event.target.files;
      if (files.length > 0) {
        var fileName = files[0].name;
        var fileExtension = fileName.split(".").pop().toLowerCase();

        if (fileExtension === "pdf") {
          fileNameSpan.textContent = fileName;
          filePreview.classList.remove("hidden");
          uploadArea.classList.add("hidden");
        } else {
          alert("Hanya file PDF yang diizinkan.");
          filePreview.classList.add("hidden");
        }
      }
    });
  }

  if (removeFileButton) {
    removeFileButton.addEventListener("click", function () {
      fileInput.value = "";
      filePreview.classList.add("hidden");
      uploadArea.classList.remove("hidden");
      downloadLink.classList.add("hidden");
    });
  }

  if (convertButton) {
    convertButton.addEventListener("click", function () {
      var formData = new FormData();
      var file = fileInput.files[0];
      if (file) {
        formData.append("pdfFile", file);

        fetch("/upload", {
          method: "POST",
          body: formData,
        })
          .then((response) => response.blob())
          .then((blob) => {
            var url = window.URL.createObjectURL(blob);
            downloadLink.href = url;
            downloadLink.classList.remove("hidden");
          })
          .catch((error) => {
            console.error("Error:", error);
            alert("Terjadi kesalahan saat mengonversi file.");
          });
      } else {
        alert("Silakan pilih file terlebih dahulu.");
      }
    });
  }
});
