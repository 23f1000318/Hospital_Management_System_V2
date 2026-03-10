<script>
import { ref, computed, onMounted } from "vue";
import api from "@/utils/api";

export default {
  setup() {
    const patients = ref([]);
    const appointments = ref([]);
    const loading = ref(true);
    const error = ref("");
    const searchQuery = ref("");
    
    // View patient history modal
    const showHistoryModal = ref(false);
    const selectedPatient = ref(null);
    const patientAppointments = ref([]);

    const filteredPatients = computed(() => {
      if (!searchQuery.value) return patients.value;
      const q = searchQuery.value.toLowerCase();
      return patients.value.filter(p => 
        p.user?.name?.toLowerCase().includes(q) ||
        p.user?.email?.toLowerCase().includes(q) ||
        p.phone?.includes(searchQuery.value)
      );
    });

    const fetchData = async () => {
      try {
        // Get doctor's dashboard data which includes assigned patients
        const dashboardData = await api.get("/doctor/dashboard");
        patients.value = dashboardData.assigned_patients || [];
        
        // Get all appointments for patient history
        const allAppointments = await api.get("/appointments");
        appointments.value = allAppointments;
      } catch (e) {
        error.value = e.message;
      } finally {
        loading.value = false;
      }
    };

    const getPatientAppointments = (patientId) => {
      return appointments.value
        .filter(apt => apt.patient_id === patientId)
        .sort((a, b) => new Date(b.date) - new Date(a.date));
    };

    const viewPatientHistory = (patient) => {
      selectedPatient.value = patient;
      patientAppointments.value = getPatientAppointments(patient.id);
      showHistoryModal.value = true;
    };

    const getStatusBadge = (status) => {
      const badges = { booked: "bg-primary", completed: "bg-success", cancelled: "bg-danger" };
      return badges[status] || "bg-secondary";
    };

    onMounted(fetchData);

    return { 
      patients, filteredPatients, loading, error, searchQuery,
      showHistoryModal, selectedPatient, patientAppointments,
      viewPatientHistory, getStatusBadge
    };
  },
};
</script>

<template>
  <div class="container py-4">
    <h2 class="mb-4"><i class="bi bi-people me-2"></i>My Patients</h2>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary"></div>
    </div>

    <div v-if="error" class="alert alert-danger">{{ error }}</div>

    <!-- Search -->
    <div class="card mb-4" v-if="!loading">
      <div class="card-body">
        <div class="input-group">
          <span class="input-group-text"><i class="bi bi-search"></i></span>
          <input type="text" class="form-control" v-model="searchQuery" placeholder="Search patient by name, email, or phone...">
        </div>
      </div>
    </div>

    <div v-if="!loading && patients.length === 0" class="alert alert-info">
      <i class="bi bi-info-circle me-2"></i>No patients assigned yet. Patients will appear here after they book appointments with you.
    </div>

    <div class="row g-3" v-if="!loading && patients.length > 0">
      <div v-for="patient in filteredPatients" :key="patient.id" class="col-md-6 col-lg-4">
        <div class="card h-100 shadow-sm">
          <div class="card-body">
            <h5 class="card-title">
              <i class="bi bi-person-circle me-2 text-primary"></i>{{ patient.user?.name || "Unknown" }}
            </h5>
            <p class="card-text mb-2">
              <small class="text-muted">
                <i class="bi bi-envelope me-1"></i>{{ patient.user?.email || "N/A" }}
              </small>
            </p>
            <ul class="list-unstyled small mb-3">
              <li><i class="bi bi-telephone me-1"></i><strong>Phone:</strong> {{ patient.phone || "N/A" }}</li>
              <li><i class="bi bi-gender-ambiguous me-1"></i><strong>Gender:</strong> {{ patient.gender || "N/A" }}</li>
              <li><i class="bi bi-droplet me-1"></i><strong>Blood:</strong> {{ patient.blood_group || "N/A" }}</li>
              <li><i class="bi bi-calendar me-1"></i><strong>DOB:</strong> {{ patient.date_of_birth || "N/A" }}</li>
            </ul>
            <button class="btn btn-sm btn-outline-primary w-100" @click="viewPatientHistory(patient)">
              <i class="bi bi-clock-history me-1"></i>View History
            </button>
          </div>
        </div>
      </div>
      <div v-if="filteredPatients.length === 0" class="col-12">
        <div class="alert alert-warning">No patients match your search.</div>
      </div>
    </div>

    <!-- Patient History Modal -->
    <div v-if="showHistoryModal" class="modal d-block" style="background: rgba(0,0,0,0.5)">
      <div class="modal-dialog modal-xl">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">
              <i class="bi bi-clock-history me-2"></i>
              Patient History: {{ selectedPatient?.user?.name }}
            </h5>
            <button type="button" class="btn-close" @click="showHistoryModal = false"></button>
          </div>
          <div class="modal-body">
            <div class="row mb-3">
              <div class="col-md-6">
                <p><strong>Email:</strong> {{ selectedPatient?.user?.email }}</p>
                <p><strong>Phone:</strong> {{ selectedPatient?.phone || "N/A" }}</p>
              </div>
              <div class="col-md-6">
                <p><strong>Gender:</strong> {{ selectedPatient?.gender || "N/A" }}</p>
                <p><strong>Blood Group:</strong> {{ selectedPatient?.blood_group || "N/A" }}</p>
              </div>
            </div>
            
            <h6 class="border-bottom pb-2 mb-3">Appointment History</h6>
            <div v-if="patientAppointments.length === 0" class="text-muted">No appointments found.</div>
            <div v-else class="table-responsive">
              <table class="table table-sm">
                <thead class="table-light">
                  <tr>
                    <th>Date</th>
                    <th>Time</th>
                    <th>Reason</th>
                    <th>Status</th>
                    <th>Diagnosis</th>
                    <th>Prescription</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="apt in patientAppointments" :key="apt.id">
                    <td>{{ apt.date }}</td>
                    <td>{{ apt.time }}</td>
                    <td>{{ apt.reason || "-" }}</td>
                    <td>
                      <span class="badge" :class="getStatusBadge(apt.status)">{{ apt.status }}</span>
                    </td>
                    <td>{{ apt.treatment?.diagnosis || "-" }}</td>
                    <td>{{ apt.treatment?.prescription || "-" }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="showHistoryModal = false">Close</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
