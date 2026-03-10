<script>
import { ref, computed, onMounted } from "vue";
import api from "@/utils/api";

export default {
  setup() {
    const appointments = ref([]);
    const loading = ref(true);
    const error = ref("");
    const searchQuery = ref("");
    
    // View treatment details modal
    const showDetailModal = ref(false);
    const selectedAppointment = ref(null);

    const fetchHistory = async () => {
      try {
        const all = await api.get("/appointments");
        // Filter completed appointments
        appointments.value = all
          .filter((a) => a.status === "completed")
          .sort((a, b) => new Date(b.date) - new Date(a.date));
      } catch (e) {
        error.value = e.message;
      } finally {
        loading.value = false;
      }
    };

    const filteredAppointments = computed(() => {
      if (!searchQuery.value) return appointments.value;
      const q = searchQuery.value.toLowerCase();
      return appointments.value.filter(apt => 
        apt.doctor?.user?.name?.toLowerCase().includes(q) ||
        apt.doctor?.department?.name?.toLowerCase().includes(q) ||
        apt.treatment?.diagnosis?.toLowerCase().includes(q)
      );
    });

    const viewDetails = (apt) => {
      selectedAppointment.value = apt;
      showDetailModal.value = true;
    };

    onMounted(fetchHistory);

    return { 
      appointments, filteredAppointments, loading, error, searchQuery,
      showDetailModal, selectedAppointment, viewDetails 
    };
  },
};
</script>

<template>
  <div class="container py-4">
    <h2 class="mb-4"><i class="bi bi-file-medical me-2"></i>Medical History</h2>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary"></div>
    </div>

    <div v-if="error" class="alert alert-danger">{{ error }}</div>

    <!-- Search -->
    <div class="card mb-4" v-if="!loading && appointments.length > 0">
      <div class="card-body">
        <div class="input-group">
          <span class="input-group-text"><i class="bi bi-search"></i></span>
          <input type="text" class="form-control" v-model="searchQuery" placeholder="Search by doctor, department, or diagnosis...">
        </div>
      </div>
    </div>

    <div class="row g-3" v-if="!loading">
      <div v-for="apt in filteredAppointments" :key="apt.id" class="col-12">
        <div class="card shadow-sm">
          <div class="card-header d-flex justify-content-between align-items-center bg-success bg-opacity-10">
            <span>
              <i class="bi bi-calendar me-2 text-success"></i>
              <strong>{{ apt.date }}</strong> at {{ apt.time }}
            </span>
            <span class="badge bg-success">Completed</span>
          </div>
          <div class="card-body">
            <div class="row">
              <div class="col-md-4">
                <h5 class="card-title mb-1">
                  <i class="bi bi-person-badge me-1 text-primary"></i>
                  Dr. {{ apt.doctor?.user?.name || "Unknown" }}
                </h5>
                <p class="text-muted mb-0">
                  <i class="bi bi-building me-1"></i>{{ apt.doctor?.department?.name || "General" }}
                </p>
                <small class="text-muted">Reason: {{ apt.reason || "General checkup" }}</small>
              </div>
              
              <div class="col-md-8" v-if="apt.treatment">
                <div class="row">
                  <div class="col-md-6">
                    <p class="mb-1"><strong><i class="bi bi-clipboard-pulse me-1"></i>Diagnosis:</strong></p>
                    <p class="small mb-2">{{ apt.treatment.diagnosis || "N/A" }}</p>
                  </div>
                  <div class="col-md-6">
                    <p class="mb-1"><strong><i class="bi bi-capsule me-1"></i>Prescription:</strong></p>
                    <p class="small mb-2">{{ apt.treatment.prescription?.substring(0, 100) || "N/A" }}{{ apt.treatment.prescription?.length > 100 ? '...' : '' }}</p>
                  </div>
                </div>
                <div v-if="apt.treatment.follow_up_date" class="mt-2">
                  <span class="badge bg-info">
                    <i class="bi bi-calendar-check me-1"></i>Follow-up: {{ apt.treatment.follow_up_date }}
                  </span>
                </div>
                <button class="btn btn-sm btn-outline-primary mt-2" @click="viewDetails(apt)">
                  <i class="bi bi-eye me-1"></i>View Full Details
                </button>
              </div>
              <div class="col-md-8" v-else>
                <p class="text-muted mb-0"><i>No treatment details recorded</i></p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="!loading && appointments.length === 0" class="text-center text-muted py-5">
      <i class="bi bi-file-medical display-4"></i>
      <p class="mt-3">No medical history found.</p>
      <p>Your completed appointments with treatment details will appear here.</p>
    </div>

    <div v-if="!loading && filteredAppointments.length === 0 && appointments.length > 0" class="alert alert-warning text-center">
      <i class="bi bi-search me-2"></i>No results found for "{{ searchQuery }}"
    </div>

    <!-- Detail Modal -->
    <div v-if="showDetailModal" class="modal d-block" style="background: rgba(0,0,0,0.5)">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header bg-success text-white">
            <h5 class="modal-title">
              <i class="bi bi-file-medical me-2"></i>Treatment Details
            </h5>
            <button type="button" class="btn-close btn-close-white" @click="showDetailModal = false"></button>
          </div>
          <div class="modal-body">
            <div class="row mb-4">
              <div class="col-md-6">
                <p><strong>Date:</strong> {{ selectedAppointment?.date }} at {{ selectedAppointment?.time }}</p>
                <p><strong>Doctor:</strong> Dr. {{ selectedAppointment?.doctor?.user?.name }}</p>
                <p><strong>Department:</strong> {{ selectedAppointment?.doctor?.department?.name }}</p>
              </div>
              <div class="col-md-6">
                <p><strong>Reason for Visit:</strong> {{ selectedAppointment?.reason || 'General checkup' }}</p>
                <p v-if="selectedAppointment?.treatment?.follow_up_date">
                  <strong>Follow-up Date:</strong> 
                  <span class="badge bg-info">{{ selectedAppointment?.treatment?.follow_up_date }}</span>
                </p>
              </div>
            </div>
            
            <div v-if="selectedAppointment?.treatment">
              <div class="card mb-3">
                <div class="card-header"><i class="bi bi-clipboard-pulse me-2"></i>Diagnosis</div>
                <div class="card-body">
                  <p class="mb-0">{{ selectedAppointment?.treatment?.diagnosis || 'No diagnosis recorded' }}</p>
                </div>
              </div>
              
              <div class="card mb-3">
                <div class="card-header"><i class="bi bi-capsule me-2"></i>Prescription</div>
                <div class="card-body">
                  <p class="mb-0" style="white-space: pre-wrap">{{ selectedAppointment?.treatment?.prescription || 'No prescription recorded' }}</p>
                </div>
              </div>
              
              <div class="card" v-if="selectedAppointment?.treatment?.notes">
                <div class="card-header"><i class="bi bi-sticky me-2"></i>Doctor's Notes</div>
                <div class="card-body">
                  <p class="mb-0">{{ selectedAppointment?.treatment?.notes }}</p>
                </div>
              </div>
            </div>
            <div v-else class="text-center text-muted py-4">
              <i class="bi bi-exclamation-circle display-4"></i>
              <p class="mt-2">No treatment details recorded for this appointment</p>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="showDetailModal = false">Close</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
