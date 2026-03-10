<script>
import { ref, computed, onMounted } from "vue";
import api from "@/utils/api";

export default {
  setup() {
    const patients = ref([]);
    const loading = ref(true);
    const error = ref("");
    const successMsg = ref("");
    
    // Search
    const searchQuery = ref("");
    
    // Edit modal
    const showEditModal = ref(false);
    const editForm = ref({
      id: null,
      phone: "",
      address: "",
      gender: "",
      blood_group: "",
      date_of_birth: "",
    });
    const editLoading = ref(false);

    // View profile modal
    const showProfileModal = ref(false);
    const viewingPatient = ref(null);
    const patientStats = ref(null);
    const patientTreatments = ref([]);
    const profileLoading = ref(false);

    const viewProfile = async (patient) => {
      showProfileModal.value = true;
      viewingPatient.value = patient;
      patientStats.value = null;
      patientTreatments.value = [];
      profileLoading.value = true;
      
      try {
        const data = await api.get(`/admin/patients/${patient.id}/profile`);
        patientStats.value = data.stats;
        patientTreatments.value = data.treatments || [];
      } catch (e) {
        console.error("Failed to load patient details", e);
      } finally {
        profileLoading.value = false;
      }
    };

    const filteredPatients = computed(() => {
      if (!searchQuery.value) return patients.value;
      
      const q = searchQuery.value.toLowerCase();
      return patients.value.filter(patient => 
        patient.user?.name?.toLowerCase().includes(q) ||
        patient.user?.email?.toLowerCase().includes(q) ||
        patient.phone?.includes(q)
      );
    });

    const fetchPatients = async () => {
      try {
        patients.value = await api.get("/patients");
      } catch (e) {
        error.value = e.message;
      } finally {
        loading.value = false;
      }
    };

    const openEditModal = (patient) => {
      editForm.value = {
        id: patient.id,
        phone: patient.phone || "",
        address: patient.address || "",
        gender: patient.gender || "",
        blood_group: patient.blood_group || "",
        date_of_birth: patient.date_of_birth || "",
      };
      showEditModal.value = true;
    };

    const savePatient = async () => {
      editLoading.value = true;
      error.value = "";
      try {
        await api.put(`/patients/${editForm.value.id}`, {
          phone: editForm.value.phone,
          address: editForm.value.address,
          gender: editForm.value.gender,
          blood_group: editForm.value.blood_group,
          date_of_birth: editForm.value.date_of_birth,
        });
        showEditModal.value = false;
        successMsg.value = "Patient updated successfully!";
        setTimeout(() => successMsg.value = "", 3000);
        fetchPatients();
      } catch (e) {
        error.value = e.message;
      } finally {
        editLoading.value = false;
      }
    };

    const toggleBlacklist = async (patient) => {
      const action = patient.user?.active ? "blacklist" : "activate";
      if (!confirm(`Are you sure you want to ${action} this patient?`)) return;
      try {
        await api.patch(`/users/${patient.user_id}/toggle-active`);
        successMsg.value = `Patient ${action}ed successfully!`;
        setTimeout(() => successMsg.value = "", 3000);
        fetchPatients();
      } catch (e) {
        error.value = e.message;
      }
    };

    const deletePatient = async (id) => {
      if (!confirm("Are you sure you want to delete this patient permanently?")) return;
      try {
        await api.delete(`/patients/${id}`);
        successMsg.value = "Patient deleted successfully!";
        setTimeout(() => successMsg.value = "", 3000);
        fetchPatients();
      } catch (e) {
        error.value = e.message;
      }
    };

    onMounted(fetchPatients);

    return { 
      patients, loading, error, successMsg,
      searchQuery, filteredPatients,
      showEditModal, editForm, editLoading,
      openEditModal, savePatient, toggleBlacklist, deletePatient,
      showProfileModal, viewingPatient, viewProfile,
      patientStats, patientTreatments, profileLoading
    };
  },
};
</script>

<template>
  <div class="container py-4">
    <h2 class="mb-4"><i class="bi bi-people me-2"></i>Manage Patients</h2>

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

    <!-- Search -->
    <div class="card mb-4" v-if="!loading">
      <div class="card-body">
        <div class="row g-3">
          <div class="col-md-10">
            <div class="input-group">
              <span class="input-group-text"><i class="bi bi-search"></i></span>
              <input type="text" class="form-control" v-model="searchQuery" placeholder="Search by name, email, or phone...">
            </div>
          </div>
          <div class="col-md-2">
            <button class="btn btn-outline-secondary w-100" @click="searchQuery = ''">
              <i class="bi bi-x-circle me-1"></i>Clear
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Patients Table -->
    <div class="table-responsive" v-if="!loading">
      <table class="table table-striped table-hover">
        <thead class="table-dark">
          <tr>
            <th>ID</th>
            <th>Name</th>
            <th>Email</th>
            <th>Phone</th>
            <th>Gender</th>
            <th>Blood Group</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="patient in filteredPatients" :key="patient.id" :class="{ 'table-secondary': !patient.user?.active }">
            <td>{{ patient.id }}</td>
            <td>{{ patient.user?.name || "N/A" }}</td>
            <td>{{ patient.user?.email || "N/A" }}</td>
            <td>{{ patient.phone || "N/A" }}</td>
            <td>{{ patient.gender || "N/A" }}</td>
            <td>{{ patient.blood_group || "N/A" }}</td>
            <td>
              <span :class="patient.user?.active ? 'badge bg-success' : 'badge bg-danger'">
                {{ patient.user?.active ? 'Active' : 'Blacklisted' }}
              </span>
            </td>
            <td>
              <div class="btn-group btn-group-sm">
                <button class="btn btn-outline-info" @click="viewProfile(patient)" title="View Profile">
                  <i class="bi bi-eye"></i>
                </button>
                <button class="btn btn-outline-primary" @click="openEditModal(patient)" title="Edit" :disabled="!patient.user?.active">
                  <i class="bi bi-pencil"></i>
                </button>
                <button class="btn" :class="patient.user?.active ? 'btn-outline-warning' : 'btn-outline-success'" @click="toggleBlacklist(patient)" :title="patient.user?.active ? 'Blacklist' : 'Activate'">
                  <i :class="patient.user?.active ? 'bi bi-slash-circle' : 'bi bi-check-circle'"></i>
                </button>
                <button class="btn btn-outline-danger" @click="deletePatient(patient.id)" title="Delete">
                  <i class="bi bi-trash"></i>
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="filteredPatients.length === 0">
            <td colspan="8" class="text-center text-muted py-4">No patients found.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Edit Modal -->
    <div class="modal fade show" :class="{ 'd-block': showEditModal }" tabindex="-1" v-if="showEditModal">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title"><i class="bi bi-pencil me-2"></i>Edit Patient</h5>
            <button type="button" class="btn-close" @click="showEditModal = false"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <label class="form-label">Phone</label>
              <input type="tel" class="form-control" v-model="editForm.phone" placeholder="Phone number">
            </div>
            <div class="mb-3">
              <label class="form-label">Address</label>
              <textarea class="form-control" v-model="editForm.address" rows="2" placeholder="Address"></textarea>
            </div>
            <div class="mb-3">
              <label class="form-label">Gender</label>
              <select class="form-select" v-model="editForm.gender">
                <option value="">Select Gender</option>
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
              </select>
            </div>
            <div class="mb-3">
              <label class="form-label">Blood Group</label>
              <select class="form-select" v-model="editForm.blood_group">
                <option value="">Select Blood Group</option>
                <option value="A+">A+</option>
                <option value="A-">A-</option>
                <option value="B+">B+</option>
                <option value="B-">B-</option>
                <option value="AB+">AB+</option>
                <option value="AB-">AB-</option>
                <option value="O+">O+</option>
                <option value="O-">O-</option>
              </select>
            </div>
            <div class="mb-3">
              <label class="form-label">Date of Birth</label>
              <input type="date" class="form-control" v-model="editForm.date_of_birth">
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="showEditModal = false">Cancel</button>
            <button type="button" class="btn btn-primary" @click="savePatient" :disabled="editLoading">
              <span v-if="editLoading" class="spinner-border spinner-border-sm me-1"></span>
              Save Changes
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade show" v-if="showEditModal" @click="showEditModal = false"></div>

    <!-- Profile Modal -->
    <div class="modal fade show d-block" tabindex="-1" v-if="showProfileModal">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Patient Profile</h5>
            <button type="button" class="btn-close" @click="showProfileModal = false"></button>
          </div>
          <div class="modal-body">
            <div class="text-center mb-3">
              <h5>{{ viewingPatient?.user?.name }}</h5>
              <span :class="viewingPatient?.user?.active ? 'badge bg-success' : 'badge bg-danger'">
                {{ viewingPatient?.user?.active ? 'Active' : 'Blacklisted' }}
              </span>
            </div>
            
            <div class="row mb-3">
              <div class="col-md-6">
                <table class="table table-sm">
                  <tr><th>Email</th><td>{{ viewingPatient?.user?.email || 'N/A' }}</td></tr>
                  <tr><th>Phone</th><td>{{ viewingPatient?.phone || 'N/A' }}</td></tr>
                  <tr><th>Gender</th><td>{{ viewingPatient?.gender || 'N/A' }}</td></tr>
                </table>
              </div>
              <div class="col-md-6">
                <table class="table table-sm">
                  <tr><th>Blood Group</th><td>{{ viewingPatient?.blood_group || 'N/A' }}</td></tr>
                  <tr><th>Date of Birth</th><td>{{ viewingPatient?.date_of_birth || 'N/A' }}</td></tr>
                  <tr><th>Address</th><td>{{ viewingPatient?.address || 'N/A' }}</td></tr>
                </table>
              </div>
            </div>
            
            <!-- Stats -->
            <div v-if="profileLoading" class="text-center py-3">
              <div class="spinner-border spinner-border-sm"></div>
            </div>
            <div v-else-if="patientStats" class="row g-2 mb-3">
              <div class="col-3">
                <div class="card text-center">
                  <div class="card-body py-2">
                    <h5 class="mb-0">{{ patientStats.total_appointments }}</h5>
                    <small class="text-muted">Total</small>
                  </div>
                </div>
              </div>
              <div class="col-3">
                <div class="card text-center">
                  <div class="card-body py-2">
                    <h5 class="mb-0 text-success">{{ patientStats.completed }}</h5>
                    <small class="text-muted">Completed</small>
                  </div>
                </div>
              </div>
              <div class="col-3">
                <div class="card text-center">
                  <div class="card-body py-2">
                    <h5 class="mb-0 text-primary">{{ patientStats.booked }}</h5>
                    <small class="text-muted">Upcoming</small>
                  </div>
                </div>
              </div>
              <div class="col-3">
                <div class="card text-center">
                  <div class="card-body py-2">
                    <h5 class="mb-0 text-danger">{{ patientStats.cancelled }}</h5>
                    <small class="text-muted">Cancelled</small>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Treatment History -->
            <div v-if="patientTreatments.length > 0">
              <h6>Treatment History</h6>
              <div class="table-responsive" style="max-height: 200px; overflow-y: auto;">
                <table class="table table-sm">
                  <thead class="table-light">
                    <tr>
                      <th>Date</th>
                      <th>Doctor</th>
                      <th>Diagnosis</th>
                      <th>Prescription</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="t in patientTreatments" :key="t.appointment_id">
                      <td>{{ t.date }}</td>
                      <td>{{ t.doctor_name }}</td>
                      <td>{{ t.diagnosis || '-' }}</td>
                      <td>{{ t.prescription || '-' }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            <div v-else-if="!profileLoading" class="text-muted text-center py-2">
              No treatment history found.
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="showProfileModal = false">Close</button>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade show" v-if="showProfileModal" @click="showProfileModal = false"></div>
  </div>
</template>

<style scoped>
.modal.show {
  background: rgba(0,0,0,0.5);
}
</style>
