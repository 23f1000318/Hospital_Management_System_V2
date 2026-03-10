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

    const dashboardData = ref(null);
    const loading = ref(true);
    const error = ref("");
    const successMsg = ref("");
    
    // Treatment modal
    const showTreatmentModal = ref(false);
    const selectedAppointment = ref(null);
    const treatmentForm = ref({
      diagnosis: "",
      prescription: "",
      notes: "",
      follow_up_date: "",
    });
    const treatmentLoading = ref(false);
    
    // Availability modal
    const showAvailabilityModal = ref(false);
    const availabilityData = ref({});
    const availabilityLoading = ref(false);
    const lockedDates = ref(new Set());
    
    const todayDate = formatLocalDate(new Date());

    // View tabs
    const activeTab = ref("today");

    const next7Days = computed(() => {
      const days = [];
      const today = new Date();
      for (let i = 0; i < 7; i++) {
        const date = new Date(today);
        date.setDate(today.getDate() + i);
        const dateStr = formatLocalDate(date);
        const dayName = date.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });
        days.push({ date: dateStr, label: dayName });
      }
      return days;
    });

    const timeSlots = ["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00", "20:00", "21:00"];

    const fetchDashboard = async () => {
      try {
        dashboardData.value = await api.get("/doctor/dashboard");
      } catch (e) {
        error.value = e.message;
      } finally {
        loading.value = false;
      }
    };

    const updateStatus = async (appointmentId, status) => {
      const action = status === "completed" ? "mark as completed" : "cancel";
      if (!confirm(`Are you sure you want to ${action} this appointment?`)) return;
      
      try {
        await api.patch(`/doctor/appointments/${appointmentId}/status`, { status });
        successMsg.value = `Appointment ${status} successfully!`;
        setTimeout(() => successMsg.value = "", 3000);
        fetchDashboard();
      } catch (e) {
        error.value = e.message;
      }
    };

    const openTreatmentModal = (apt) => {
      selectedAppointment.value = apt;
      // Pre-fill if treatment already exists
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
        fetchDashboard();
      } catch (e) {
        error.value = e.message;
      } finally {
        treatmentLoading.value = false;
      }
    };

    // lockedSlots: Set of "date|time" strings for slots already saved
    const lockedSlots = ref(new Set());

    const isSlotLocked = (date, time) => lockedSlots.value.has(`${date}|${time}`);

    const isSlotPast = (date, time) => {
      if (date !== todayDate) return false;
      const now = new Date();
      const currentMinutes = now.getHours() * 60 + now.getMinutes();
      const [h, m] = time.split(":").map(Number);
      return h * 60 + m <= currentMinutes;
    };

    const isSlotDisabled = (date, time) => isSlotLocked(date, time) || isSlotPast(date, time);

    const openAvailabilityModal = async () => {
      availabilityLoading.value = true;
      try {
        const res = await api.get("/doctor/availability");
        availabilityData.value = JSON.parse(res.availability || "{}");
        // Lock individual saved slots
        const saved = new Set();
        for (const [date, slots] of Object.entries(availabilityData.value)) {
          for (const time of slots) {
            saved.add(`${date}|${time}`);
          }
        }
        lockedSlots.value = saved;
      } catch (e) {
        availabilityData.value = {};
        lockedSlots.value = new Set();
      }
      availabilityLoading.value = false;
      showAvailabilityModal.value = true;
    };

    const toggleSlot = (date, time) => {
      if (isSlotDisabled(date, time)) return;
      if (!availabilityData.value[date]) {
        availabilityData.value[date] = [];
      }
      const idx = availabilityData.value[date].indexOf(time);
      if (idx === -1) {
        availabilityData.value[date].push(time);
      } else {
        availabilityData.value[date].splice(idx, 1);
      }
    };

    const isSlotSelected = (date, time) => {
      return availabilityData.value[date]?.includes(time) || false;
    };

    const saveAvailability = async () => {
      availabilityLoading.value = true;
      error.value = "";
      try {
        await api.put("/doctor/availability", { availability: JSON.stringify(availabilityData.value) });
        // Lock all newly saved slots
        const saved = new Set(lockedSlots.value);
        for (const [date, slots] of Object.entries(availabilityData.value)) {
          for (const time of slots) {
            saved.add(`${date}|${time}`);
          }
        }
        lockedSlots.value = saved;
        showAvailabilityModal.value = false;
        successMsg.value = "Availability updated successfully!";
        setTimeout(() => successMsg.value = "", 3000);
      } catch (e) {
        error.value = e.message;
      } finally {
        availabilityLoading.value = false;
      }
    };

    const getStatusBadge = (status) => {
      const badges = { booked: "bg-primary", completed: "bg-success", cancelled: "bg-danger" };
      return badges[status] || "bg-secondary";
    };

    const isTreatmentFormValid = computed(() => {
      return treatmentForm.value.diagnosis?.trim() && treatmentForm.value.prescription?.trim();
    });

    onMounted(fetchDashboard);

    return {
      dashboardData, loading, error, successMsg,
      activeTab, showTreatmentModal, selectedAppointment,
      treatmentForm, treatmentLoading, showAvailabilityModal,
      availabilityData, availabilityLoading, next7Days, timeSlots,
      todayDate, fetchDashboard, updateStatus, openTreatmentModal, saveTreatment,
      openAvailabilityModal, toggleSlot, isSlotSelected, isSlotDisabled, isSlotLocked, isSlotPast, saveAvailability,
      getStatusBadge, isTreatmentFormValid
    };
  },
};
</script>

<template>
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2>Dashboard</h2>
      <button class="btn btn-primary btn-sm" @click="openAvailabilityModal">
        Set Availability
      </button>
    </div>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary"></div>
    </div>

    <div v-if="error" class="alert alert-danger alert-dismissible py-2">
      {{ error }}
      <button type="button" class="btn-close" @click="error = ''"></button>
    </div>

    <div v-if="successMsg" class="alert alert-success alert-dismissible py-2">
      {{ successMsg }}
      <button type="button" class="btn-close" @click="successMsg = ''"></button>
    </div>

    <div v-if="dashboardData && !loading">
      <!-- Stats Cards -->
      <div class="row g-3 mb-4">
        <div class="col-6 col-md-3">
          <div class="card border-0 h-100" style="background: #f0f9ff;">
            <div class="card-body text-center py-3">
              <h3 class="mb-0 text-primary">{{ dashboardData.stats.today_count }}</h3>
              <small class="text-muted">Today</small>
            </div>
          </div>
        </div>
        <div class="col-6 col-md-3">
          <div class="card border-0 h-100" style="background: #fef3c7;">
            <div class="card-body text-center py-3">
              <h3 class="mb-0" style="color: #d97706;">{{ dashboardData.stats.week_count }}</h3>
              <small class="text-muted">This Week</small>
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
          <div class="card border-0 h-100" style="background: #fce7f3;">
            <div class="card-body text-center py-3">
              <h3 class="mb-0" style="color: #db2777;">{{ dashboardData.stats.total_patients }}</h3>
              <small class="text-muted">Patients</small>
            </div>
          </div>
        </div>
      </div>

      <!-- Tabs -->
      <ul class="nav nav-tabs mb-3">
        <li class="nav-item">
          <button class="nav-link" :class="{ active: activeTab === 'today' }" @click="activeTab = 'today'">
            Today ({{ dashboardData.stats.today_count }})
          </button>
        </li>
        <li class="nav-item">
          <button class="nav-link" :class="{ active: activeTab === 'week' }" @click="activeTab = 'week'">
            This Week ({{ dashboardData.stats.week_count }})
          </button>
        </li>
        <li class="nav-item">
          <button class="nav-link" :class="{ active: activeTab === 'patients' }" @click="activeTab = 'patients'">
            Patients ({{ dashboardData.stats.total_patients }})
          </button>
        </li>
      </ul>

      <!-- Today's Appointments -->
      <div v-if="activeTab === 'today'">
        <div class="card">
          <div class="card-header">Today's Appointments</div>
          <div class="card-body p-0">
            <div v-if="dashboardData.today_appointments.length === 0" class="text-center text-muted py-4">
              No appointments scheduled for today.
            </div>
            <div class="table-responsive" v-else>
              <table class="table table-hover mb-0">
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Patient</th>
                    <th>Reason</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="apt in dashboardData.today_appointments" :key="apt.id">
                    <td><strong>{{ apt.time }}</strong></td>
                    <td>{{ apt.patient?.user?.name || "N/A" }}</td>
                    <td>{{ apt.reason || "-" }}</td>
                    <td>
                      <span class="badge" :class="getStatusBadge(apt.status)">{{ apt.status }}</span>
                    </td>
                    <td>
                      <div class="btn-group btn-group-sm" v-if="apt.status === 'booked' && apt.date === todayDate">
                        <button class="btn btn-outline-success" @click="openTreatmentModal(apt)">Treat</button>
                        <button class="btn btn-outline-danger" @click="updateStatus(apt.id, 'cancelled')">Cancel</button>
                      </div>
                      <button v-else-if="apt.status === 'completed'" class="btn btn-sm btn-outline-secondary" @click="openTreatmentModal(apt)">
                        View
                      </button>
                      <span v-else class="text-muted">-</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <!-- Week's Appointments -->
      <div v-if="activeTab === 'week'">
        <div class="card">
          <div class="card-header">Upcoming Appointments</div>
          <div class="card-body p-0">
            <div v-if="dashboardData.week_appointments.length === 0" class="text-center text-muted py-4">
              No upcoming appointments.
            </div>
            <div class="table-responsive" v-else>
              <table class="table table-hover mb-0">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Time</th>
                    <th>Patient</th>
                    <th>Reason</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="apt in dashboardData.week_appointments" :key="apt.id">
                    <td>{{ apt.date }}</td>
                    <td><strong>{{ apt.time }}</strong></td>
                    <td>{{ apt.patient?.user?.name || "N/A" }}</td>
                    <td>{{ apt.reason || "-" }}</td>
                    <td>
                      <span class="badge" :class="getStatusBadge(apt.status)">{{ apt.status }}</span>
                    </td>
                    <td>
                      <div class="btn-group btn-group-sm" v-if="apt.status === 'booked' && apt.date === todayDate">
                        <button class="btn btn-outline-success" @click="openTreatmentModal(apt)">Treat</button>
                        <button class="btn btn-outline-danger" @click="updateStatus(apt.id, 'cancelled')">Cancel</button>
                      </div>
                      <div v-else-if="apt.status === 'booked' && apt.date > todayDate">
                        <button class="btn btn-sm btn-outline-danger" @click="updateStatus(apt.id, 'cancelled')">Cancel</button>
                      </div>
                      <button v-else-if="apt.status === 'completed'" class="btn btn-sm btn-outline-secondary" @click="openTreatmentModal(apt)">
                        View
                      </button>
                      <span v-else class="text-muted">-</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <!-- My Patients -->
      <div v-if="activeTab === 'patients'">
        <div class="card">
          <div class="card-header">My Patients</div>
          <div class="card-body p-0">
            <div v-if="dashboardData.assigned_patients.length === 0" class="text-center text-muted py-4">
              No patients assigned yet.
            </div>
            <div class="table-responsive" v-else>
              <table class="table table-hover mb-0">
                <thead class="table-light">
                  <tr>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Phone</th>
                    <th>Gender</th>
                    <th>Blood Group</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="patient in dashboardData.assigned_patients" :key="patient.id">
                    <td>{{ patient.user?.name || "N/A" }}</td>
                    <td>{{ patient.user?.email || "N/A" }}</td>
                    <td>{{ patient.phone || "-" }}</td>
                    <td>{{ patient.gender || "-" }}</td>
                    <td>{{ patient.blood_group || "-" }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Treatment Modal -->
    <div class="modal fade show d-block" tabindex="-1" v-if="showTreatmentModal">
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
              <textarea class="form-control" v-model="treatmentForm.diagnosis" rows="3" placeholder="Enter diagnosis..." required></textarea>
            </div>
            <div class="mb-3">
              <label class="form-label">Prescription <span class="text-danger">*</span></label>
              <textarea class="form-control" v-model="treatmentForm.prescription" rows="3" placeholder="Enter prescription details..." required></textarea>
            </div>
            <div class="mb-3">
              <label class="form-label">Notes</label>
              <textarea class="form-control" v-model="treatmentForm.notes" rows="2" placeholder="Additional notes..."></textarea>
            </div>
            <div class="mb-3">
              <label class="form-label">Follow-up Date</label>
              <input type="date" class="form-control" v-model="treatmentForm.follow_up_date">
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="showTreatmentModal = false">Cancel</button>
            <button type="button" class="btn btn-primary" @click="saveTreatment" :disabled="treatmentLoading || !isTreatmentFormValid">
              <span v-if="treatmentLoading" class="spinner-border spinner-border-sm me-1"></span>
              Save Treatment
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade show" v-if="showTreatmentModal" @click="showTreatmentModal = false"></div>

    <!-- Availability Modal -->
    <div class="modal fade show d-block" tabindex="-1" v-if="showAvailabilityModal">
      <div class="modal-dialog modal-xl">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title"><i class="bi bi-calendar-plus me-2"></i>Set Availability (Next 7 Days)</h5>
            <button type="button" class="btn-close" @click="showAvailabilityModal = false"></button>
          </div>
          <div class="modal-body">
            <p class="text-muted mb-3">Click on time slots to toggle availability. Selected slots are shown in green.</p>
            <div class="table-responsive">
              <table class="table table-bordered text-center">
                <thead class="table-dark">
                  <tr>
                    <th>Time</th>
                    <th v-for="day in next7Days" :key="day.date">
                      {{ day.label }}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="time in timeSlots" :key="time">
                    <td class="fw-bold">{{ time }}</td>
                    <td v-for="day in next7Days" :key="day.date + time"
                        :style="isSlotDisabled(day.date, time) ? 'background-color: #f0f0f0; opacity: 0.7;' : ''">
                      <button
                        class="btn btn-sm w-100"
                        :class="isSlotSelected(day.date, time) ? 'btn-success' : 'btn-outline-secondary'"
                        :disabled="isSlotDisabled(day.date, time)"
                        @click="toggleSlot(day.date, time)"
                        :title="isSlotLocked(day.date, time) ? 'Already saved' : isSlotPast(day.date, time) ? 'Time already passed' : ''"
                      >
                        <i v-if="isSlotLocked(day.date, time)" class="bi bi-lock-fill small"></i>
                        <span v-else>{{ isSlotSelected(day.date, time) ? '✓' : '-' }}</span>
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="showAvailabilityModal = false">Cancel</button>
            <button type="button" class="btn btn-primary" @click="saveAvailability" :disabled="availabilityLoading">
              <span v-if="availabilityLoading" class="spinner-border spinner-border-sm me-1"></span>
              Save Availability
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade show" v-if="showAvailabilityModal" @click="showAvailabilityModal = false"></div>
  </div>
</template>

<style scoped>
.modal.show {
  background: rgba(0,0,0,0.5);
}
</style>
