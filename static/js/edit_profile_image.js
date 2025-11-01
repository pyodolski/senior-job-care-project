// 이미지 미리보기 기능
document
  .getElementById("profileImageInput")
  .addEventListener("change", function (e) {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = function (e) {
        document.getElementById("previewImg").src = e.target.result;
        document
          .getElementById("imagePreview")
          .classList.remove("hidden");
      };
      reader.readAsDataURL(file);
    }
  });
