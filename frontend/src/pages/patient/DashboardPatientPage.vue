<script>
import { ref, computed, onMounted } from "vue";
import api from "@/utils/api";
import { useRouter } from "vue-router";

export default {
  setup() {
    const router = useRouter();
    const dashboardData = ref(null);
    const loading = ref(true);
    const error = ref("");
    const successMsg = ref("");
    
    // Department filter
    const selectedDepartment = ref("");

    // Export state
    const exporting = ref(false);
    const exportTaskId = ref("");
    const exportStatus = ref("");
    const showExportModal = ref(false);
    const exportHistory = ref([]);
    const loadingExports = ref(false);

    const filteredDoctors = computed(() => {
      if (!dashboardData.value) return [];
      let doctors = dashboardData.value.doctors || [];
      
      // Filter out blacklisted doctors
      doctors = doctors.filter(d => d.user?.active !== false);
      
      if (selectedDepartment.value) {
        doctors = doctors.filter(d => d.department_id == selectedDepartment.value);
      }
      
      return doctors;
    });

    const fetchDashboard = async () => {
      try {
        dashboardData.value = await api.get("/patient/dashboard");
      } catch (e) {
        error.value = e.message;
      } finally {
        loading.value = false;
      }
    };

    const getStatusBadge = (status) => {
      const badges = { booked: "bg-primary", completed: "bg-success", cancelled: "bg-danger" };
      return badges[status] || "bg-secondary";
    };

    const goToFindDoctors = () => {
      router.push("/patient/doctors");
    };

    const goToAppointments = () => {
      router.push("/patient/appointments");
    };

    const goToHistory = () => {
      router.push("/patient/history");
    };

    // Export functions
    const triggerExport = async () => {
      exporting.value = true;
      exportStatus.value = "Starting export...";
      try {
        const result = await api.post("/patient/export");
        exportTaskId.value = result.task_id;
        exportStatus.value = "Export in progress. You will receive an email when ready.";
        successMsg.value = "Export started! Check your email for notification.";
        // Poll for status
        pollExportStatus(result.task_id);
      } catch (e) {
        error.value = "Failed to start export: " + e.message;
        exporting.value = false;
      }
    };

    const pollExportStatus = async (taskId) => {
      try {
        const status = await api.get(`/exports/status/${taskId}`);
        if (status.ready) {
          exporting.value = false;
          if (status.result?.status === "completed") {
            exportStatus.value = "Export completed! You can download it below.";
            await fetchExportHistory();
          } else {
            exportStatus.value = "Export failed: " + (status.result?.message || "Unknown error");
          }
        } else {
          exportStatus.value = status.meta?.status || "Processing...";
          // Poll again in 2 seconds
          setTimeout(() => pollExportStatus(taskId), 2000);
        }
      } catch (e) {
        exporting.value = false;
        exportStatus.value = "Could not check status";
      }
    };

    const fetchExportHistory = async () => {
      loadingExports.value = true;
      try {
        const result = await api.get("/patient/exports");
        exportHistory.value = result.exports || [];
      } catch (e) {
        console.error("Failed to fetch export history", e);
      } finally {
        loadingExports.value = false;
      }
    };

    const openExportModal = async () => {
      showExportModal.value = true;
      await fetchExportHistory();
    };

    const downloadExport = (filename) => {
      // Use direct download via token
      const token = api.getToken();
      const url = `${api.getBaseURL()}/exports/download/${filename}`;
      
      // Create a temporary link with auth header workaround
      fetch(url, {
        headers: { "Authentication-Token": token }
      })
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
          }
          return response.blob();
        })
        .then(blob => {
          const link = document.createElement("a");
          link.href = URL.createObjectURL(blob);
          link.download = filename;
          link.click();
        })
        .catch(e => {
          error.value = "Download failed: " + e.message;
        });
    };

    onMounted(fetchDashboard);

    return {
      dashboardData, loading, error, successMsg,
      selectedDepartment, filteredDoctors,
      getStatusBadge, goToFindDoctors, goToAppointments, goToHistory,
      // Export
      exporting, exportTaskId, exportStatus, showExportModal,
      exportHistory, loadingExports,
      triggerExport, openExportModal, downloadExport, fetchExportHistory
    };
  },
};
</script>

<template>
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2>Dashboard</h2>
      <router-link to="/patient/profile" class="btn btn-outline-primary btn-sm">
        My Profile
      </router-link>
    </div>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary"></div>
    </div>

    <div v-if="error" class="alert alert-danger">{{ error }}</div>

    <div v-if="dashboardData && !loading">
      <!-- Stats Cards -->
      <div class="row g-3 mb-4">
        <div class="col-6 col-md-3">
          <div class="card border-0 h-100" style="background: #f0f9ff;">
            <div class="card-body text-center py-3">
              <h3 class="mb-0 text-primary">{{ dashboardData.stats.upcoming_count }}</h3>
              <small class="text-muted">Upcoming</small>
            </div>
          </div>
        </div>
        <div class="col-6 col-md-3">
          <div class="card border-0 h-100" style="background: #f0fdf4;">
            <div class="card-body text-center py-3">
              <h3 class="mb-0 text-success">{{ dashboardData.stats.completed }}</h3>
              <small class="text-muted">Completed</small>
            </div>
          </div>
        </div>
        <div class="col-6 col-md-3">
          <div class="card border-0 h-100" style="background: #fef3c7;">
            <div class="card-body text-center py-3">
              <h3 class="mb-0" style="color: #d97706;">{{ dashboardData.departments?.length || 0 }}</h3>
              <small class="text-muted">Departments</small>
            </div>
          </div>
        </div>
        <div class="col-6 col-md-3">
          <div class="card border-0 h-100" style="background: #fce7f3;">
            <div class="card-body text-center py-3">
              <h3 class="mb-0" style="color: #db2777;">{{ filteredDoctors?.length || 0 }}</h3>
              <small class="text-muted">Doctors</small>
            </div>
          </div>
        </div>
      </div>

      <!-- Quick Links -->
      <div class="d-flex flex-wrap gap-2 mb-4">
        <button class="btn btn-primary btn-sm" @click="goToFindDoctors">Find Doctors</button>
        <button class="btn btn-outline-secondary btn-sm" @click="goToAppointments">My Appointments</button>
        <button class="btn btn-outline-secondary btn-sm" @click="goToHistory">Medical History</button>
        <button class="btn btn-outline-secondary btn-sm" @click="openExportModal">Export Records</button>
      </div>

      <div class="row g-4">
        <!-- Left Column: Departments & Doctors -->
        <div class="col-lg-7">
          <!-- Departments -->
          <div class="card mb-4">
            <div class="card-header">
              Departments
              <span class="float-end badge bg-secondary">{{ dashboardData.departments?.length || 0 }}</span>
            </div>
            <div class="card-body">
              <div class="d-flex flex-wrap gap-2">
                <button v-for="dept in dashboardData.departments" :key="dept.id" 
                  class="btn btn-sm"
                  :class="selectedDepartment == dept.id ? 'btn-primary' : 'btn-outline-secondary'"
                  @click="selectedDepartment = selectedDepartment == dept.id ? '' : dept.id">
                  {{ dept.name }}
                </button>
              </div>
              <div v-if="dashboardData.departments?.length === 0" class="text-muted text-center py-3">
                No departments available.
              </div>
            </div>
          </div>

          <!-- Available Doctors -->
          <div class="card">
            <div class="card-header d-flex justify-content-between align-items-center">
              <span>Available Doctors</span>
              <span class="badge bg-primary">{{ filteredDoctors.length }}</span>
            </div>
            <div class="card-body p-0">
              <div v-if="filteredDoctors.length === 0" class="text-muted text-center py-4">
                No doctors available{{ selectedDepartment ? ' in this department' : '' }}.
              </div>
              <div class="list-group list-group-flush">
                <div v-for="doc in filteredDoctors.slice(0, 5)" :key="doc.id" class="list-group-item">
                  <div class="d-flex justify-content-between align-items-center">
                    <div>
                      <strong>Dr. {{ doc.user?.name || 'Unknown' }}</strong>
                      <br>
                      <small class="text-muted">
                        {{ doc.department?.name }} &bull; {{ doc.experience_years || 0 }}y exp &bull; ₹{{ doc.consultation_fee || 0 }}
                      </small>
                    </div>
                    <router-link :to="`/patient/doctors?doctor=${doc.id}`" class="btn btn-sm btn-primary">
                      Book
                    </router-link>
                  </div>
                </div>
              </div>
              <div class="card-footer text-center" v-if="filteredDoctors.length > 5">
                <router-link to="/patient/doctors" class="text-decoration-none">View all doctors →</router-link>
              </div>
            </div>
          </div>
        </div>

        <!-- Right Column: Appointments -->
        <div class="col-lg-5">
          <!-- Upcoming Appointments -->
          <div class="card mb-4">
            <div class="card-header">
              Upcoming Appointments
            </div>
            <div class="card-body p-0">
              <div v-if="dashboardData.upcoming_appointments?.length === 0" class="text-muted text-center py-4">
                No upcoming appointments.
                <br><router-link to="/patient/doctors">Book one now</router-link>
              </div>
              <div class="list-group list-group-flush">
                <div v-for="apt in dashboardData.upcoming_appointments" :key="apt.id" class="list-group-item">
                  <div class="d-flex justify-content-between align-items-center">
                    <div>
                      <strong>{{ apt.date }}</strong> at {{ apt.time }}
                      <br><small class="text-muted">Dr. {{ apt.doctor?.user?.name || 'N/A' }}</small>
                    </div>
                    <span class="badge" :class="getStatusBadge(apt.status)">{{ apt.status }}</span>
                  </div>
                </div>
              </div>
              <div class="card-footer text-center" v-if="dashboardData.upcoming_appointments?.length > 0">
                <router-link to="/patient/appointments" class="text-decoration-none">View all →</router-link>
              </div>
            </div>
          </div>

          <!-- Recent History -->
          <div class="card">
            <div class="card-header">
              Recent Visits
            </div>
            <div class="card-body p-0">
              <div v-if="dashboardData.past_appointments?.length === 0" class="text-muted text-center py-4">
                No past appointments.
              </div>
              <div class="list-group list-group-flush">
                <div v-for="apt in dashboardData.past_appointments" :key="apt.id" class="list-group-item">
                  <div class="d-flex justify-content-between align-items-center">
                    <div>
                      <strong>{{ apt.date }}</strong>
                      <br><small class="text-muted">Dr. {{ apt.doctor?.user?.name || 'N/A' }}</small>
                    </div>
                    <span class="badge" :class="getStatusBadge(apt.status)">{{ apt.status }}</span>
                  </div>
                </div>
              </div>
              <div class="card-footer text-center" v-if="dashboardData.past_appointments?.length > 0">
                <router-link to="/patient/history" class="text-decoration-none">View full history →</router-link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Export Modal -->
    <div v-if="showExportModal" class="modal d-block" style="background: rgba(0,0,0,0.5)">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Export Records</h5>
            <button type="button" class="btn-close" @click="showExportModal = false"></button>
          </div>
          <div class="modal-body">
            <p class="text-muted mb-3">Generate a CSV file with your treatment history.</p>
            
            <div v-if="exportStatus" class="alert alert-info py-2" style="font-size: 0.875rem;">
              {{ exportStatus }}
            </div>
            
            <button class="btn btn-primary w-100" @click="triggerExport" :disabled="exporting">
              <span v-if="exporting" class="spinner-border spinner-border-sm me-2"></span>
              {{ exporting ? 'Exporting...' : 'Export as CSV' }}
            </button>
            <p class="small text-muted mt-2 mb-0">You'll receive an email when ready.</p>

            <!-- Export History -->
            <div v-if="exportHistory.length > 0" class="mt-4">
              <h6 class="text-muted mb-2">Previous Exports</h6>
              <div class="list-group">
                <div v-for="exp in exportHistory" :key="exp.filename" class="list-group-item d-flex justify-content-between align-items-center">
                  <div>
                    <strong style="font-size: 0.875rem;">{{ exp.filename }}</strong>
                    <br><small class="text-muted">{{ Math.round(exp.size_bytes / 1024) }} KB</small>
                  </div>
                  <button class="btn btn-sm btn-outline-primary" @click="downloadExport(exp.filename)">Download</button>
                </div>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="showExportModal = false">Close</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
