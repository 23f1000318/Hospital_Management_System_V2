<script>
import { useUserStore } from "@/stores/user";

export default {
  setup() {
    const userStore = useUserStore();
    return { userStore };
  },
};
</script>

<template>
  <div>
    <!-- Hero Section -->
    <div class="bg-primary text-white py-5">
      <div class="container py-4">
        <div class="row align-items-center">
          <div class="col-lg-7">
            <h1 class="display-5 fw-bold mb-3">Healthcare Made Simple</h1>
            <p class="lead opacity-75 mb-4">
              Book appointments, connect with doctors, and manage your health records — all in one place.
            </p>
            <div v-if="!userStore.isAuthenticated">
              <router-link to="/signup" class="btn btn-light btn-lg me-2 px-4">
                Get Started
              </router-link>
              <router-link to="/login" class="btn btn-outline-light btn-lg px-4">
                Sign In
              </router-link>
            </div>
            <div v-else>
              <p class="mb-0 opacity-75">Welcome back, <strong>{{ userStore.user?.name }}</strong></p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Features -->
    <div class="container py-5">
      <div class="row g-4">
        <div class="col-md-4">
          <div class="card h-100 border-0 shadow-sm">
            <div class="card-body p-4">
              <div class="rounded-2 d-inline-flex align-items-center justify-content-center mb-3" style="width: 48px; height: 48px; background: #dbeafe;">
                <i class="bi bi-calendar-check text-primary" style="font-size: 1.25rem;"></i>
              </div>
              <h5 class="fw-semibold mb-2">Easy Scheduling</h5>
              <p class="text-muted mb-0" style="font-size: 0.9375rem;">
                Book appointments online. Choose your doctor and preferred time slot.
              </p>
            </div>
          </div>
        </div>
        <div class="col-md-4">
          <div class="card h-100 border-0 shadow-sm">
            <div class="card-body p-4">
              <div class="rounded-2 d-inline-flex align-items-center justify-content-center mb-3" style="width: 48px; height: 48px; background: #d1fae5;">
                <i class="bi bi-people text-success" style="font-size: 1.25rem;"></i>
              </div>
              <h5 class="fw-semibold mb-2">Expert Doctors</h5>
              <p class="text-muted mb-0" style="font-size: 0.9375rem;">
                Access specialists across departments. View profiles and qualifications.
              </p>
            </div>
          </div>
        </div>
        <div class="col-md-4">
          <div class="card h-100 border-0 shadow-sm">
            <div class="card-body p-4">
              <div class="rounded-2 d-inline-flex align-items-center justify-content-center mb-3" style="width: 48px; height: 48px; background: #fef3c7;">
                <i class="bi bi-shield-check" style="font-size: 1.25rem; color: #d97706;"></i>
              </div>
              <h5 class="fw-semibold mb-2">Secure Records</h5>
              <p class="text-muted mb-0" style="font-size: 0.9375rem;">
                Your medical history and treatment records, safely stored and accessible.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
