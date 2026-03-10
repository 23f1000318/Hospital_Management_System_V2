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
    const activeTab = ref("upcoming");

    const fetchAppointments = async () => {
      try {
        appointments.value = await api.get("/appointments");
      } catch (e) {
        error.value = e.message;
      } finally {
        loading.value = false;
      }
    };

    const today = formatLocalDate(new Date());

    const upcomingAppointments = computed(() => {
      return appointments.value
        .filter(apt => apt.status === "booked" && apt.date >= today)
        .sort((a, b) => new Date(a.date + ' ' + a.time) - new Date(b.date + ' ' + b.time));
    });

    const pastAppointments = computed(() => {
      return appointments.value
        .filter(apt => apt.status !== "booked" || apt.date < today)
        .sort((a, b) => new Date(b.date + ' ' + b.time) - new Date(a.date + ' ' + a.time));
    });

    const getStatusBadge = (status) => {
      const badges = {
        booked: "bg-primary",
        completed: "bg-success",
        cancelled: "bg-danger",
      };
      return badges[status] || "bg-secondary";
    };

    const cancelAppointment = async (id) => {
      if (!confirm("Are you sure you want to cancel this appointment?")) return;
      try {
        await api.patch(`/patient/appointments/${id}/cancel`);
        successMsg.value = "Appointment cancelled successfully!";
        setTimeout(() => successMsg.value = "", 3000);
        fetchAppointments();
      } catch (e) {
        error.value = e.message;
      }
    };

    const isUpcoming = (apt) => {
      return apt.status === "booked" && apt.date >= today;
    };

    onMounted(fetchAppointments);

    return { 
      appointments, loading, error, successMsg, activeTab,
      upcomingAppointments, pastAppointments,
      getStatusBadge, cancelAppointment, isUpcoming 
    };
  },
};
</script>

<template>
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2><i class="bi bi-calendar-check me-2"></i>My Appointments</h2>
      <router-link to="/patient/doctors" class="btn btn-primary">
        <i class="bi bi-plus-circle me-1"></i>Book New
      </router-link>
    </div>

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

    <div v-if="!loading">
      <!-- Tabs -->
      <ul class="nav nav-tabs mb-4">
        <li class="nav-item">
          <button class="nav-link" :class="{ active: activeTab === 'upcoming' }" @click="activeTab = 'upcoming'">
            <i class="bi bi-calendar-event me-1"></i>
            Upcoming ({{ upcomingAppointments.length }})
          </button>
        </li>
        <li class="nav-item">
          <button class="nav-link" :class="{ active: activeTab === 'past' }" @click="activeTab = 'past'">
            <i class="bi bi-clock-history me-1"></i>
            Past/Completed ({{ pastAppointments.length }})
          </button>
        </li>
      </ul>

      <!-- Upcoming Appointments -->
      <div v-if="activeTab === 'upcoming'">
        <div v-if="upcomingAppointments.length === 0" class="text-center text-muted py-5">
          <i class="bi bi-calendar-x display-4"></i>
          <p class="mt-3">No upcoming appointments.</p>
          <router-link to="/patient/doctors" class="btn btn-primary">
            <i class="bi bi-search me-1"></i>Find a Doctor
          </router-link>
        </div>

        <div class="row g-3" v-else>
          <div v-for="apt in upcomingAppointments" :key="apt.id" class="col-md-6 col-lg-4">
            <div class="card h-100 border-primary">
              <div class="card-header bg-primary text-white d-flex justify-content-between">
                <span><i class="bi bi-calendar me-1"></i>{{ apt.date }}</span>
                <span><i class="bi bi-clock me-1"></i>{{ apt.time }}</span>
              </div>
              <div class="card-body">
                <h5 class="card-title">
                  <i class="bi bi-person-badge me-1 text-primary"></i>
                  Dr. {{ apt.doctor?.user?.name || "N/A" }}
                </h5>
                <p class="text-muted mb-2">
                  <i class="bi bi-building me-1"></i>{{ apt.doctor?.department?.name || "General" }}
                </p>
                <p class="small mb-2">
                  <strong>Reason:</strong> {{ apt.reason || "General checkup" }}
                </p>
                <span class="badge" :class="getStatusBadge(apt.status)">{{ apt.status }}</span>
              </div>
              <div class="card-footer">
                <button 
                  class="btn btn-outline-danger w-100"
                  @click="cancelAppointment(apt.id)"
                >
                  <i class="bi bi-x-circle me-1"></i>Cancel Appointment
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Past Appointments -->
      <div v-if="activeTab === 'past'">
        <div v-if="pastAppointments.length === 0" class="text-center text-muted py-5">
          <i class="bi bi-clock-history display-4"></i>
          <p class="mt-3">No past appointments.</p>
        </div>

        <div class="table-responsive" v-else>
          <table class="table table-hover">
            <thead class="table-light">
              <tr>
                <th>Date</th>
                <th>Time</th>
                <th>Doctor</th>
                <th>Department</th>
                <th>Reason</th>
                <th>Status</th>
                <th>Diagnosis</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="apt in pastAppointments" :key="apt.id">
                <td>{{ apt.date }}</td>
                <td>{{ apt.time }}</td>
                <td>Dr. {{ apt.doctor?.user?.name || "N/A" }}</td>
                <td>{{ apt.doctor?.department?.name || "N/A" }}</td>
                <td>{{ apt.reason || "-" }}</td>
                <td>
                  <span class="badge" :class="getStatusBadge(apt.status)">{{ apt.status }}</span>
                </td>
                <td>
                  <span v-if="apt.status === 'completed' && apt.treatment" class="text-success">
                    <i class="bi bi-check-circle me-1"></i>
                    {{ apt.treatment.diagnosis?.substring(0, 30) || 'Treated' }}...
                  </span>
                  <span v-else-if="apt.status === 'cancelled'" class="text-muted">-</span>
                  <span v-else class="text-muted">Pending</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        
        <div class="text-center mt-3" v-if="pastAppointments.length > 0">
          <router-link to="/patient/history" class="btn btn-outline-primary">
            <i class="bi bi-file-medical me-1"></i>View Full Medical History
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>
