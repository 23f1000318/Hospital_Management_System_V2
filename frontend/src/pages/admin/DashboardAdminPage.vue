<script>
import { ref, onMounted } from "vue";
import api from "@/utils/api";

export default {
  setup() {
    const stats = ref({});
    const loading = ref(true);
    const error = ref("");

    const fetchDashboard = async () => {
      try {
        stats.value = await api.get("/dashboard");
      } catch (e) {
        error.value = e.message;
      } finally {
        loading.value = false;
      }
    };

    onMounted(fetchDashboard);

    return { stats, loading, error };
  },
};
</script>

<template>
  <div class="container py-4">
    <h2 class="mb-4">Dashboard</h2>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary"></div>
    </div>

    <div v-if="error" class="alert alert-danger">{{ error }}</div>

    <div v-if="!loading">
      <!-- Stats Cards -->
      <div class="row g-3 mb-4">
        <div class="col-6 col-md-3">
          <div class="card border-0 h-100" style="background: #f0f9ff;">
            <div class="card-body">
              <p class="text-muted mb-1" style="font-size: 0.8125rem;">Doctors</p>
              <h3 class="mb-0 text-primary">{{ stats.total_doctors }}</h3>
            </div>
          </div>
        </div>
        <div class="col-6 col-md-3">
          <div class="card border-0 h-100" style="background: #f0fdf4;">
            <div class="card-body">
              <p class="text-muted mb-1" style="font-size: 0.8125rem;">Patients</p>
              <h3 class="mb-0 text-success">{{ stats.total_patients }}</h3>
            </div>
          </div>
        </div>
        <div class="col-6 col-md-3">
          <div class="card border-0 h-100" style="background: #fef3c7;">
            <div class="card-body">
              <p class="text-muted mb-1" style="font-size: 0.8125rem;">Departments</p>
              <h3 class="mb-0" style="color: #d97706;">{{ stats.total_departments }}</h3>
            </div>
          </div>
        </div>
        <div class="col-6 col-md-3">
          <div class="card border-0 h-100" style="background: #fce7f3;">
            <div class="card-body">
              <p class="text-muted mb-1" style="font-size: 0.8125rem;">Appointments</p>
              <h3 class="mb-0" style="color: #db2777;">{{ stats.total_appointments }}</h3>
            </div>
          </div>
        </div>
      </div>

      <!-- Appointments Breakdown -->
      <div class="card">
        <div class="card-header">Appointments Overview</div>
        <div class="card-body py-4">
          <div class="row text-center">
            <div class="col-4">
              <h3 class="text-primary mb-1">{{ stats.booked_appointments }}</h3>
              <small class="text-muted">Upcoming</small>
            </div>
            <div class="col-4">
              <h3 class="text-success mb-1">{{ stats.completed_appointments }}</h3>
              <small class="text-muted">Completed</small>
            </div>
            <div class="col-4">
              <h3 class="text-danger mb-1">{{ stats.cancelled_appointments }}</h3>
              <small class="text-muted">Cancelled</small>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
