<script>
import { ref, computed, onMounted } from "vue";
import api from "@/utils/api";

export default {
  setup() {
    const appointments = ref([]);
    const loading = ref(true);
    const error = ref("");
    
    // Filters
    const filterStatus = ref("");
    const filterTimeframe = ref("all");
    const searchQuery = ref("");

    // Patient History Modal
    const showHistoryModal = ref(false);
    const historyLoading = ref(false);
    const historyPatient = ref(null);
    const patientHistory = ref([]);

    const filteredAppointments = computed(() => {
      let result = appointments.value;
      
      // Filter by status
      if (filterStatus.value) {
        result = result.filter(apt => apt.status === filterStatus.value);
      }
      
      // Filter by timeframe
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      
      if (filterTimeframe.value === "upcoming") {
        result = result.filter(apt => {
          const aptDate = new Date(apt.date);
          aptDate.setHours(0, 0, 0, 0);
          return aptDate > today && apt.status === "booked";
        });
      } else if (filterTimeframe.value === "past") {
        result = result.filter(apt => {
          const aptDate = new Date(apt.date);
          aptDate.setHours(0, 0, 0, 0);
          return aptDate < today || apt.status === "completed" || apt.status === "cancelled";
        });
      } else if (filterTimeframe.value === "today") {
        result = result.filter(apt => {
          const aptDate = new Date(apt.date);
          aptDate.setHours(0, 0, 0, 0);
          return aptDate.getTime() === today.getTime();
        });
      }
      
      // Search
      if (searchQuery.value) {
        const q = searchQuery.value.toLowerCase();
        result = result.filter(apt => 
          apt.patient?.user?.name?.toLowerCase().includes(q) ||
          apt.doctor?.user?.name?.toLowerCase().includes(q)
        );
      }
      
      // Sort by date descending (newest first)
      return result.sort((a, b) => new Date(b.date) - new Date(a.date));
    });

    const stats = computed(() => {
      const total = appointments.value.length;
      const booked = appointments.value.filter(a => a.status === "booked").length;
      const completed = appointments.value.filter(a => a.status === "completed").length;
      const cancelled = appointments.value.filter(a => a.status === "cancelled").length;
      return { total, booked, completed, cancelled };
    });

    const fetchAppointments = async () => {
      try {
        appointments.value = await api.get("/appointments");
      } catch (e) {
        error.value = e.message;
      } finally {
        loading.value = false;
      }
    };

    const getStatusBadge = (status) => {
      const badges = {
        booked: "bg-primary",
        completed: "bg-success",
        cancelled: "bg-danger",
      };
      return badges[status] || "bg-secondary";
    };

    const clearFilters = () => {
      filterStatus.value = "";
      filterTimeframe.value = "all";
      searchQuery.value = "";
    };

    const viewPatientHistory = async (apt) => {
      historyPatient.value = apt.patient;
      showHistoryModal.value = true;
      historyLoading.value = true;
      patientHistory.value = [];
      
      try {
        const data = await api.get(`/admin/patients/${apt.patient.id}/history`);
        patientHistory.value = data.treatments || [];
      } catch (e) {
        patientHistory.value = [];
      } finally {
        historyLoading.value = false;
      }
    };

    const closeHistoryModal = () => {
      showHistoryModal.value = false;
      historyPatient.value = null;
      patientHistory.value = [];
    };

    onMounted(fetchAppointments);

    return { 
      appointments, loading, error, 
      filterStatus, filterTimeframe, searchQuery,
      filteredAppointments, stats, getStatusBadge, clearFilters,
      showHistoryModal, historyLoading, historyPatient, patientHistory,
      viewPatientHistory, closeHistoryModal
    };
  },
};
</script>

<template>
  <div class="container py-4">
    <h2 class="mb-4"><i class="bi bi-calendar-check me-2"></i>All Appointments</h2>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary"></div>
    </div>

    <div v-if="error" class="alert alert-danger">{{ error }}</div>

    <!-- Stats Cards -->
    <div class="row g-3 mb-4" v-if="!loading">
      <div class="col-6 col-md-3">
        <div class="card text-center border-0" style="background: #f1f5f9;">
          <div class="card-body py-3">
            <h3 class="mb-0">{{ stats.total }}</h3>
            <small class="text-muted">Total</small>
          </div>
        </div>
      </div>
      <div class="col-6 col-md-3">
        <div class="card text-center border-0" style="background: #dbeafe;">
          <div class="card-body py-3">
            <h3 class="mb-0 text-primary">{{ stats.booked }}</h3>
            <small class="text-muted">Booked</small>
          </div>
        </div>
      </div>
      <div class="col-6 col-md-3">
        <div class="card text-center border-0" style="background: #d1fae5;">
          <div class="card-body py-3">
            <h3 class="mb-0 text-success">{{ stats.completed }}</h3>
            <small class="text-muted">Completed</small>
          </div>
        </div>
      </div>
      <div class="col-6 col-md-3">
        <div class="card text-center border-0" style="background: #fee2e2;">
          <div class="card-body py-3">
            <h3 class="mb-0 text-danger">{{ stats.cancelled }}</h3>
            <small class="text-muted">Cancelled</small>
          </div>
        </div>
      </div>
    </div>

    <!-- Filters -->
    <div class="card mb-4" v-if="!loading">
      <div class="card-body">
        <div class="row g-3">
          <div class="col-md-4">
            <div class="input-group">
              <span class="input-group-text"><i class="bi bi-search"></i></span>
              <input type="text" class="form-control" v-model="searchQuery" placeholder="Search patient or doctor...">
            </div>
          </div>
          <div class="col-md-3">
            <select class="form-select" v-model="filterStatus">
              <option value="">All Status</option>
              <option value="booked">Booked</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
          <div class="col-md-3">
            <select class="form-select" v-model="filterTimeframe">
              <option value="all">All Time</option>
              <option value="today">Today</option>
              <option value="upcoming">Upcoming</option>
              <option value="past">Past</option>
            </select>
          </div>
          <div class="col-md-2">
            <button class="btn btn-outline-secondary w-100" @click="clearFilters">
              <i class="bi bi-x-circle me-1"></i>Clear
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="table-responsive" v-if="!loading">
      <table class="table table-striped table-hover">
        <thead class="table-dark">
          <tr>
            <th>ID</th>
            <th>Patient</th>
            <th>Doctor</th>
            <th>Department</th>
            <th>Date</th>
            <th>Time</th>
            <th>Status</th>
            <th>History</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="apt in filteredAppointments" :key="apt.id">
            <td>{{ apt.id }}</td>
            <td>{{ apt.patient?.user?.name || "N/A" }}</td>
            <td>{{ apt.doctor?.user?.name || "N/A" }}</td>
            <td>{{ apt.doctor?.department?.name || "N/A" }}</td>
            <td>{{ apt.date }}</td>
            <td>{{ apt.time }}</td>
            <td>
              <span class="badge" :class="getStatusBadge(apt.status)">
                {{ apt.status }}
              </span>
            </td>
            <td>
              <button class="btn btn-sm btn-outline-info" @click="viewPatientHistory(apt)" :disabled="!apt.patient">
                <i class="bi bi-clock-history me-1"></i>View
              </button>
            </td>
          </tr>
          <tr v-if="filteredAppointments.length === 0">
            <td colspan="8" class="text-center text-muted py-4">No appointments found.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Patient History Modal -->
    <div v-if="showHistoryModal" class="modal fade show d-block" tabindex="-1" style="background: rgba(0,0,0,0.5);">
      <div class="modal-dialog modal-lg modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header bg-info text-white">
            <h5 class="modal-title">
              <i class="bi bi-clock-history me-2"></i>
              Patient History - {{ historyPatient?.user?.name }}
            </h5>
            <button type="button" class="btn-close btn-close-white" @click="closeHistoryModal"></button>
          </div>
          <div class="modal-body">
            <div v-if="historyLoading" class="text-center py-4">
              <div class="spinner-border text-info"></div>
              <p class="mt-2">Loading history...</p>
            </div>
            
            <div v-else-if="patientHistory.length === 0" class="text-center py-4">
              <i class="bi bi-inbox display-4 text-muted"></i>
              <p class="text-muted mt-2">No treatment history found for this patient.</p>
            </div>
            
            <div v-else>
              <div class="table-responsive">
                <table class="table table-bordered">
                  <thead class="table-light">
                    <tr>
                      <th>Visit #</th>
                      <th>Date</th>
                      <th>Doctor</th>
                      <th>Diagnosis</th>
                      <th>Prescription</th>
                      <th>Notes</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(treatment, idx) in patientHistory" :key="treatment.id">
                      <td>{{ idx + 1 }}</td>
                      <td>{{ treatment.date || treatment.appointment?.date || '-' }}</td>
                      <td>{{ treatment.doctor?.user?.name || treatment.appointment?.doctor?.user?.name || '-' }}</td>
                      <td>{{ treatment.diagnosis || '-' }}</td>
                      <td>{{ treatment.prescription || '-' }}</td>
                      <td>{{ treatment.notes || '-' }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeHistoryModal">Close</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
