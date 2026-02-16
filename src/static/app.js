document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");
  let messageTimeout;

  function showMessage(text, variant = "info") {
    messageDiv.textContent = text;
    messageDiv.className = variant;
    messageDiv.classList.remove("hidden");

    if (messageTimeout) {
      clearTimeout(messageTimeout);
    }

    messageTimeout = setTimeout(() => {
      messageDiv.classList.add("hidden");
    }, 5000);
  }

  function attachParticipantRemovalHandlers() {
    const deleteButtons = document.querySelectorAll(".delete-icon");
    deleteButtons.forEach((button) => {
      button.addEventListener("click", handleParticipantRemoval);
    });
  }

  async function handleParticipantRemoval(event) {
    const button = event.currentTarget;
    const activityName = button.dataset.activity;
    const email = button.dataset.email;

    button.disabled = true;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activityName)}/unregister?email=${encodeURIComponent(email)}`,
        {
          method: "DELETE",
        }
      );

      const result = await response.json().catch(() => ({}));

      if (response.ok) {
        showMessage(result.message || "Participant removed", "success");
        await fetchActivities();
      } else {
        showMessage(result.detail || "Failed to remove participant.", "error");
      }
    } catch (error) {
      console.error("Error removing participant:", error);
      showMessage("Failed to remove participant.", "error");
    } finally {
      button.disabled = false;
    }
  }

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      // Add cache busting to ensure fresh data
      const response = await fetch("/activities?" + new Date().getTime(), {
        cache: 'no-cache'
      });
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";
      activitySelect.innerHTML = '<option value="">-- Select an activity --</option>';

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - details.participants.length;
        
        // Create participants list HTML with delete actions
        const hasParticipants = details.participants && details.participants.length > 0;
        const participantItems = hasParticipants
          ? details.participants
              .map(
                (participantEmail) => `
                  <div class="participant-item">
                    <span class="participant-email">${participantEmail}</span>
                    <button
                      type="button"
                      class="delete-icon"
                      title="Remove participant"
                      aria-label="Remove ${participantEmail}"
                      data-activity="${name}"
                      data-email="${participantEmail}"
                    >&times;</button>
                  </div>
                `
              )
              .join("")
          : "";

        const participantsSection = hasParticipants
          ? `
            <div class="participants-section">
              <p><strong>Current Participants:</strong></p>
              <div class="participants-list">
                ${participantItems}
              </div>
            </div>
          `
          : `
            <div class="participants-section">
              <p><strong>Current Participants:</strong></p>
              <p class="no-participants">No one signed up yet</p>
            </div>
          `;

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          ${participantsSection}
        `;

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });

      attachParticipantRemovalHandlers();
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        signupForm.reset();
        await fetchActivities();
        showMessage(result.message, "success");
      } else {
        showMessage(result.detail || "An error occurred", "error");
      }
    } catch (error) {
      showMessage("Failed to sign up. Please try again.", "error");
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  fetchActivities();
});
