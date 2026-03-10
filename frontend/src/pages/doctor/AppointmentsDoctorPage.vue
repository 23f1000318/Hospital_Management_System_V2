<script>
import { ref, computed, onMounted } from "vue";
import api from "@/utils/api";

export default {
  setup() {
    const formatLocalDate = (dateObj) => {
      const y = dateObj.getFullYear();
      const m = String(dateObj.getMonth() + 1).padStart(2, "0");
      const d = String(dateObj.getDate()).padStart(2, "0");
      return `${y}-${m}-${d}`;
    };

    const appointments = ref([]);
    const loading = ref(true);
    const error = ref("");
    const successMsg = ref("");
    const showTreatmentModal = ref(false);
    const selectedAppointment = ref(null);
    const treatmentForm = ref({
      diagnosis: "",
      prescription: "",
      notes: "",
      follow_up_date: "",
    });
    const treatmentLoading = ref(false);
    
    // Filters
    const filterStatus = ref("");
    const filterTimeframe = ref("all");

    const todayDate = formatLocalDate(new Date());

    const filteredAppointments = computed(() => {
      let result = appointments.value;
      const today = todayDate;

      if (filterTimeframe.value === "today") {
        result = result.filter(apt => apt.date === today && ["booked", "completed", "cancelled"].includes(apt.status));
      } else if (filterTimeframe.value === "upcoming") {
        result = result.filter(apt => apt.date > today && ["booked", "cancelled"].includes(apt.status));
      } else if (filterTimeframe.value === "past") {
        result = result.filter(apt => apt.date < today && ["cancelled", "completed"].includes(apt.status));
      }

      if (filterStatus.value) {
        result = result.filter(apt => apt.status === filterStatus.value);
      }

      return result.sort((a, b) => new Date(b.date) - new Date(a.date));
    });

    const canTreat = (apt) => apt.status === "booked" && apt.date === todayDate;
    const canCancelOnly = (apt) => apt.status === "booked" && apt.date > todayDate;

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

    const updateStatus = async (aptId, status) => {
      const action = status === "completed" ? "mark as completed" : "cancel";
      if (!confirm(`Are you sure you want to ${action} this appointment?`)) return;
      
      try {
        await api.patch(`/doctor/appointments/${aptId}/status`, { status });
        successMsg.value = `Appointment ${status} successfully!`;
        setTimeout(() => successMsg.value = "", 3000);
        fetchAppointments();
      } catch (e) {
        error.value = e.message;
      }
    };

    const openTreatmentModal = (apt) => {
      selectedAppointment.value = apt;
      if (apt.treatment) {
        treatmentForm.value = {
          diagnosis: apt.treatment.diagnosis || "",
          prescription: apt.treatment.prescription || "",
          notes: apt.treatment.notes || "",
          follow_up_date: apt.treatment.follow_up_date || "",
        };
      } else {
        treatmentForm.value = { diagnosis: "", prescription: "", notes: "", follow_up_date: "" };
      }
      showTreatmentModal.value = true;
    };

    const saveTreatment = async () => {
      treatmentLoading.value = true;
      error.value = "";
      try {
        await api.post(`/doctor/appointments/${selectedAppointment.value.id}/treatment`, treatmentForm.value);
        showTreatmentModal.value = false;
        successMsg.value = "Treatment saved successfully!";
        setTimeout(() => successMsg.value = "", 3000);
        fetchAppointments();
      } catch (e) {
        error.value = e.message;
      } finally {
        treatmentLoading.value = false;
      }
    };

    const clearFilters = () => {
      filterStatus.value = "";
      filterTimeframe.value = "all";
    };

    const isTreatmentFormValid = computed(() => {
      return treatmentForm.value.diagnosis?.trim() && treatmentForm.value.prescription?.trim();
    });

    onMounted(fetchAppointments);

    return {
      appointments, filteredAppointments, loading, error, successMsg,
      filterStatus, filterTimeframe, getStatusBadge, updateStatus,
      showTreatmentModal, selectedAppointment, treatmentForm, treatmentLoading,
      openTreatmentModal, saveTreatment, clearFilters, isTreatmentFormValid,
      canTreat, canCancelOnly,
    };
  },
};
</script>

<template>
  <div class="container py-4">
    <h2 class="mb-4"><i class="bi bi-calendar-check me-2"></i>All My Appointments</h2>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary"></div>
    </div>

    <div v-if="error" class="alert alert-danger alert-dismissible">
      {{ error }}
      <button type="button" class="btn-close" @click="error = ''"></button>
    </div>

    <div v-if="successMsg" class="alert alert-success alert-dismissible">
      {{ successMsg }}
      <button type="button" class="btn-close" @click="successMsg = ''"></button>
    </div>

    <!-- Filters -->
    <div class="card mb-4" v-if="!loading">
      <div class="card-body">
        <div class="row g-3">
          <div class="col-md-4">
            <select class="form-select" v-model="filterStatus">
              <option value="">All Status</option>
              <option value="booked">Booked</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
          <div class="col-md-4">
            <select class="form-select" v-model="filterTimeframe">
              <option value="all">All Time</option>
              <option value="today">Today</option>
              <option value="upcoming">Upcoming</option>
              <option value="past">Past</option>
            </select>
          </div>
          <div class="col-md-4">
            <button class="btn btn-outline-secondary" @click="clearFilters">
              <i class="bi bi-x-circle me-1"></i>Clear Filters
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
            <th>Date</th>
            <th>Time</th>
            <th>Reason</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="apt in filteredAppointments" :key="apt.id">
            <td>{{ apt.id }}</td>
            <td>{{ apt.patient?.user?.name || "N/A" }}</td>
            <td>{{ apt.date }}</td>
            <td>{{ apt.time }}</td>
            <td>{{ apt.reason || "-" }}</td>
            <td>
              <span class="badge" :class="getStatusBadge(apt.status)">
                {{ apt.status }}
              </span>
            </td>
            <td>
              <div class="btn-group btn-group-sm" v-if="canTreat(apt)">
                <button class="btn btn-outline-success" @click="openTreatmentModal(apt)" title="Add Treatment">
                  <i class="bi bi-clipboard-pulse me-1"></i>Treat
                </button>
                <button class="btn btn-outline-danger" @click="updateStatus(apt.id, 'cancelled')" title="Cancel">
                  <i class="bi bi-x-lg"></i>
                </button>
              </div>
              <button v-else-if="canCancelOnly(apt)" class="btn btn-sm btn-outline-danger" @click="updateStatus(apt.id, 'cancelled')">
                Cancel
              </button>
              <button v-else-if="apt.status === 'completed'" class="btn btn-sm btn-outline-info" @click="openTreatmentModal(apt)">
                <i class="bi bi-eye me-1"></i>View
              </button>
              <span v-else class="text-muted">-</span>
            </td>
          </tr>
          <tr v-if="filteredAppointments.length === 0">
            <td colspan="7" class="text-center text-muted py-4">No appointments found.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Treatment Modal -->
    <div v-if="showTreatmentModal" class="modal d-block" style="background: rgba(0,0,0,0.5)">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">
              <i class="bi bi-clipboard-pulse me-2"></i>
              {{ selectedAppointment?.treatment ? 'View/Edit Treatment' : 'Add Treatment' }}
            </h5>
            <button type="button" class="btn-close" @click="showTreatmentModal = false"></button>
          </div>
          <div class="modal-body">
            <div class="alert alert-info">
              <strong>Patient:</strong> {{ selectedAppointment?.patient?.user?.name }}
              | <strong>Date:</strong> {{ selectedAppointment?.date }}
              | <strong>Reason:</strong> {{ selectedAppointment?.reason || 'N/A' }}
            </div>
            <div class="mb-3">
              <label class="form-label">Diagnosis <span class="text-danger">*</span></label>
              <textarea v-model="treatmentForm.diagnosis" class="form-control" rows="3" placeholder="Enter diagnosis..." required></textarea>
            </div>
            <div class="mb-3">
              <label class="form-label">Prescription <span class="text-danger">*</span></label>
              <textarea v-model="treatmentForm.prescription" class="form-control" rows="3" placeholder="Enter prescription details..." required></textarea>
            </div>
            <div class="mb-3">
              <label class="form-label">Notes</label>
              <textarea v-model="treatmentForm.notes" class="form-control" rows="2" placeholder="Additional notes..."></textarea>
            </div>
            <div class="mb-3">
              <label class="form-label">Follow-up Date</label>
              <input v-model="treatmentForm.follow_up_date" type="date" class="form-control" />
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="showTreatmentModal = false">Cancel</button>
            <button class="btn btn-primary" @click="saveTreatment" :disabled="treatmentLoading || !isTreatmentFormValid">
              <span v-if="treatmentLoading" class="spinner-border spinner-border-sm me-1"></span>
              Save Treatment
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
