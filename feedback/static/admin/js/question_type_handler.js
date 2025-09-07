document.addEventListener("DOMContentLoaded", function () {
  const typeField = document.getElementById("id_type");
  const optionsGroups = document.querySelectorAll(".options-group");

  function toggleOptionsVisibility() {
    const isMultipleChoice = typeField.value === "multiple-choice";

    optionsGroups.forEach((group) => {
      group.style.display = isMultipleChoice ? "block" : "none";

      const inputs = group.querySelectorAll('input[type="text"]');
      inputs.forEach((input) => {
        if (!isMultipleChoice) {
          input.value = "";
          input.required = false;
        } else {
          input.required = true;
        }
      });
    });
  }

  if (typeField && optionsGroups.length) {
    toggleOptionsVisibility();

    typeField.addEventListener("change", toggleOptionsVisibility);
  }
});
