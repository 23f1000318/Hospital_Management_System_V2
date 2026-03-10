<script>
import { ref, computed, onMounted } from "vue";
import api from "@/utils/api";

export default {
  setup() {
    const doctors = ref([]);
    const departments = ref([]);
    const loading = ref(true);
    const error = ref("");
    const successMsg = ref("");
    
    // Search and filter
    const searchQuery = ref("");
    const filterDepartment = ref("");
    
    // Add Doctor modal
    const showAddModal = ref(false);
    const addForm = ref({
      name: "",
      email: "",
      password: "",
      department_id: "",
      qualification: "",
      experience_years: 0,
      consultation_fee: 0,
    });
    const addLoading = ref(false);
    
    // Edit modal
    const showEditModal = ref(false);
    const editForm = ref({
      id: null,
      department_id: "",
      qualification: "",
      experience_years: 0,
      consultation_fee: 0,
    });
    const editLoading = ref(false);
    
    // View profile modal
    const showProfileModal = ref(false);
    const viewingDoctor = ref(null);
    const doctorStats = ref(null);
    const profileLoading = ref(false);

    const viewProfile = async (doc) => {
      showProfileModal.value = true;
      viewingDoctor.value = doc;
      doctorStats.value = null;
      profileLoading.value = true;
      
      try {
        const data = await api.get(`/admin/doctors/${doc.id}/profile`);
        doctorStats.value = data.stats;
      } catch (e) {
        console.error("Failed to load doctor details", e);
      } finally {
        profileLoading.value = false;
      }
    };

    const filteredDoctors = computed(() => {
      let result = doctors.value;
      
      if (searchQuery.value) {
        const q = searchQuery.value.toLowerCase();
        result = result.filter(doc => 
          doc.user?.name?.toLowerCase().includes(q) ||
          doc.qualification?.toLowerCase().includes(q)
        );
      }
      
      if (filterDepartment.value) {
        result = result.filter(doc => doc.department_id == filterDepartment.value);
      }
      
      return result;
    });

    const fetchData = async () => {
      try {
        const [doctorsList, deptList] = await Promise.all([
          api.get("/doctors"),
          api.get("/departments"),
        ]);
        doctors.value = doctorsList;
        departments.value = deptList;
      } catch (e) {
        error.value = e.message;
      } finally {
        loading.value = false;
      }
    };

    const openAddModal = () => {
      addForm.value = {
        name: "",
        email: "",
        password: "",
        department_id: "",
        qualification: "",
        experience_years: 0,
        consultation_fee: 0,
        phone: "",
      };
      showAddModal.value = true;
    };

    const addDoctor = async () => {
      addLoading.value = true;
      error.value = "";
      try {
        await api.post("/doctors", {
          name: addForm.value.name,
          email: addForm.value.email,
          password: addForm.value.password,
          department_id: addForm.value.department_id || null,
          qualification: addForm.value.qualification,
          experience_years: addForm.value.experience_years,
          consultation_fee: addForm.value.consultation_fee,
          phone: addForm.value.phone,
        });
        showAddModal.value = false;
        successMsg.value = "Doctor added successfully!";
        setTimeout(() => successMsg.value = "", 3000);
        fetchData();
      } catch (e) {
        error.value = e.message;
      } finally {
        addLoading.value = false;
      }
    };

    const openEditModal = (doc) => {
      editForm.value = {
        id: doc.id,
        department_id: doc.department_id || "",
        qualification: doc.qualification || "",
        experience_years: doc.experience_years || 0,
        consultation_fee: doc.consultation_fee || 0,
      };
      showEditModal.value = true;
    };

    const saveDoctor = async () => {
      editLoading.value = true;
      error.value = "";
      try {
        await api.patch(`/doctors/${editForm.value.id}`, {
          department_id: editForm.value.department_id,
          qualification: editForm.value.qualification,
          experience_years: editForm.value.experience_years,
          consultation_fee: editForm.value.consultation_fee,
        });
        showEditModal.value = false;
        successMsg.value = "Doctor updated successfully!";
        setTimeout(() => successMsg.value = "", 3000);
        fetchData();
      } catch (e) {
        error.value = e.message;
      } finally {
        editLoading.value = false;
      }
    };

    const toggleBlacklist = async (doc) => {
      const action = doc.user?.active ? "blacklist" : "activate";
      if (!confirm(`Are you sure you want to ${action} this doctor?`)) return;
      
      // Optimistically update UI
      const originalStatus = doc.user?.active;
      doc.user.active = !originalStatus;
      
      try {
        await api.patch(`/users/${doc.user_id}/toggle-active`);
        successMsg.value = `Doctor ${action}ed successfully!`;
        setTimeout(() => successMsg.value = "", 3000);
        // Refresh to get latest data
        fetchData();
      } catch (e) {
        // Revert on error
        doc.user.active = originalStatus;
        error.value = e.message;
      }
    };

    const deleteDoctor = async (id) => {
      if (!confirm("Are you sure you want to delete this doctor permanently?")) return;
      try {
        await api.delete(`/doctors/${id}`);
        successMsg.value = "Doctor deleted successfully!";
        setTimeout(() => successMsg.value = "", 3000);
        fetchData();
      } catch (e) {
        error.value = e.message;
      }
    };

    onMounted(fetchData);

    return { 
      doctors, departments, loading, error, successMsg,
      searchQuery, filterDepartment, filteredDoctors,
      showAddModal, addForm, addLoading, openAddModal, addDoctor,
      showEditModal, editForm, editLoading,
      openEditModal, saveDoctor, toggleBlacklist, deleteDoctor,
      showProfileModal, viewingDoctor, viewProfile,
      doctorStats, profileLoading
    };
  },
};
</script>

<template>
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2><i class="bi bi-person-badge me-2"></i>Manage Doctors</h2>
      <button class="btn btn-primary" @click="openAddModal">
        <i class="bi bi-plus-lg me-1"></i>Add Doctor
      </button>
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

    <!-- Search and Filter -->
    <div class="card mb-4" v-if="!loading">
      <div class="card-body">
        <div class="row g-3">
          <div class="col-md-6">
            <div class="input-group">
              <span class="input-group-text"><i class="bi bi-search"></i></span>
              <input type="text" class="form-control" v-model="searchQuery" placeholder="Search by name or qualification...">
            </div>
          </div>
          <div class="col-md-4">
            <select class="form-select" v-model="filterDepartment">
              <option value="">All Departments</option>
              <option v-for="dept in departments" :key="dept.id" :value="dept.id">{{ dept.name }}</option>
            </select>
          </div>
          <div class="col-md-2">
            <button class="btn btn-outline-secondary w-100" @click="searchQuery = ''; filterDepartment = ''">
              <i class="bi bi-x-circle me-1"></i>Clear
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Doctors Table -->
    <div class="table-responsive" v-if="!loading">
      <table class="table table-striped table-hover">
        <thead class="table-dark">
          <tr>
            <th>ID</th>
            <th>Name</th>
            <th>Email</th>
            <th>Department</th>
            <th>Qualification</th>
            <th>Experience</th>
            <th>Fee</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="doc in filteredDoctors" :key="doc.id" :class="{ 'table-secondary': !doc.user?.active }">
            <td>{{ doc.id }}</td>
            <td>{{ doc.user?.name || "N/A" }}</td>
            <td>{{ doc.user?.email || "N/A" }}</td>
            <td>{{ doc.department?.name || "N/A" }}</td>
            <td>{{ doc.qualification || "N/A" }}</td>
            <td>{{ doc.experience_years || 0 }} years</td>
            <td>₹{{ doc.consultation_fee || 0 }}</td>
            <td>
              <span :class="doc.user?.active ? 'badge bg-success' : 'badge bg-danger'">
                {{ doc.user?.active ? 'Active' : 'Blacklisted' }}
              </span>
            </td>
            <td>
              <div class="btn-group btn-group-sm">
                <button class="btn btn-outline-info" @click="viewProfile(doc)" title="View Profile">
                  <i class="bi bi-eye"></i>
                </button>
                <button class="btn btn-outline-primary" @click="openEditModal(doc)" title="Edit" :disabled="!doc.user?.active">
                  <i class="bi bi-pencil"></i>
                </button>
                <button class="btn" :class="doc.user?.active ? 'btn-outline-warning' : 'btn-outline-success'" @click="toggleBlacklist(doc)" :title="doc.user?.active ? 'Blacklist' : 'Activate'">
                  <i :class="doc.user?.active ? 'bi bi-slash-circle' : 'bi bi-check-circle'"></i>
                </button>
                <button class="btn btn-outline-danger" @click="deleteDoctor(doc.id)" title="Delete">
                  <i class="bi bi-trash"></i>
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="filteredDoctors.length === 0">
            <td colspan="9" class="text-center text-muted py-4">No doctors found.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Edit Modal -->
    <div class="modal fade show" :class="{ 'd-block': showEditModal }" tabindex="-1" v-if="showEditModal">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title"><i class="bi bi-pencil me-2"></i>Edit Doctor</h5>
            <button type="button" class="btn-close" @click="showEditModal = false"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <label class="form-label">Department</label>
              <select class="form-select" v-model="editForm.department_id">
                <option value="">Select Department</option>
                <option v-for="dept in departments" :key="dept.id" :value="dept.id">{{ dept.name }}</option>
              </select>
            </div>
            <div class="mb-3">
              <label class="form-label">Qualification</label>
              <input type="text" class="form-control" v-model="editForm.qualification" placeholder="e.g., MBBS, MD">
            </div>
            <div class="mb-3">
              <label class="form-label">Experience (years)</label>
              <input type="number" class="form-control" v-model="editForm.experience_years" min="0">
            </div>
            <div class="mb-3">
              <label class="form-label">Consultation Fee (₹)</label>
              <input type="number" class="form-control" v-model="editForm.consultation_fee" min="0">
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="showEditModal = false">Cancel</button>
            <button type="button" class="btn btn-primary" @click="saveDoctor" :disabled="editLoading">
              <span v-if="editLoading" class="spinner-border spinner-border-sm me-1"></span>
              Save Changes
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade show" v-if="showEditModal" @click="showEditModal = false"></div>

    <!-- Add Doctor Modal -->
    <div class="modal fade show" :class="{ 'd-block': showAddModal }" tabindex="-1" v-if="showAddModal">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title"><i class="bi bi-person-plus me-2"></i>Add New Doctor</h5>
            <button type="button" class="btn-close" @click="showAddModal = false"></button>
          </div>
          <div class="modal-body">
            <div class="row">
              <div class="col-md-6">
                <div class="mb-3">
                  <label class="form-label">Full Name <span class="text-danger">*</span></label>
                  <input type="text" class="form-control" v-model="addForm.name" placeholder="Dr. John Smith" required>
                </div>
              </div>
              <div class="col-md-6">
                <div class="mb-3">
                  <label class="form-label">Email <span class="text-danger">*</span></label>
                  <input type="email" class="form-control" v-model="addForm.email" placeholder="doctor@hospital.com" required>
                </div>
              </div>
            </div>
            <div class="row">
              <div class="col-md-6">
                <div class="mb-3">
                  <label class="form-label">Password <span class="text-danger">*</span></label>
                  <input type="password" class="form-control" v-model="addForm.password" placeholder="Set a password for the doctor" required>
                </div>
              </div>
              <div class="col-md-6">
                <div class="mb-3">
                  <label class="form-label">Department</label>
                  <select class="form-select" v-model="addForm.department_id">
                    <option value="">Select Department</option>
                    <option v-for="dept in departments" :key="dept.id" :value="dept.id">{{ dept.name }}</option>
                  </select>
                </div>
              </div>
            </div>
            <div class="row">
              <div class="col-md-6">
                <div class="mb-3">
                  <label class="form-label">Qualification</label>
                  <input type="text" class="form-control" v-model="addForm.qualification" placeholder="e.g., MBBS, MD">
                </div>
              </div>
              <div class="col-md-6">
                <div class="mb-3">
                  <label class="form-label">Experience (years)</label>
                  <input type="number" class="form-control" v-model="addForm.experience_years" min="0">
                </div>
              </div>
            </div>
            <div class="row">
              <div class="col-md-6">
                <div class="mb-3">
                  <label class="form-label">Phone Number</label>
                  <input type="tel" class="form-control" v-model="addForm.phone" placeholder="Phone number">
                </div>
              </div>
              <div class="col-md-6">
                <div class="mb-3">
                  <label class="form-label">Consultation Fee (₹)</label>
                  <input type="number" class="form-control" v-model="addForm.consultation_fee" min="0">
                </div>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="showAddModal = false">Cancel</button>
            <button type="button" class="btn btn-primary" @click="addDoctor" :disabled="addLoading || !addForm.name || !addForm.email || !addForm.password">
              <span v-if="addLoading" class="spinner-border spinner-border-sm me-1"></span>
              Add Doctor
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade show" v-if="showAddModal" @click="showAddModal = false"></div>

    <!-- Profile Modal -->
    <div class="modal fade show d-block" tabindex="-1" v-if="showProfileModal">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title"><i class="bi bi-person-badge me-2"></i>Doctor Profile</h5>
            <button type="button" class="btn-close" @click="showProfileModal = false"></button>
          </div>
          <div class="modal-body">
            <div v-if="profileLoading" class="text-center py-4">
              <span class="spinner-border text-primary"></span>
              <p class="mt-2 text-muted">Loading profile...</p>
            </div>
            <div v-else>
              <div class="text-center mb-3">
                <div class="bg-light rounded-circle d-inline-flex align-items-center justify-content-center" style="width: 80px; height: 80px;">
                  <i class="bi bi-person-fill text-secondary" style="font-size: 2.5rem;"></i>
                </div>
                <h5 class="mt-2">{{ viewingDoctor?.user?.name }}</h5>
                <span :class="viewingDoctor?.user?.active ? 'badge bg-success' : 'badge bg-danger'">
                  {{ viewingDoctor?.user?.active ? 'Active' : 'Blacklisted' }}
                </span>
              </div>
              
              <!-- Doctor Stats -->
              <div class="row g-2 text-center mb-4" v-if="doctorStats">
                <div class="col-4">
                  <div class="card border-0" style="background: #f0f9ff;">
                    <div class="card-body py-2">
                      <h4 class="mb-0 text-primary">{{ doctorStats.total_appointments || 0 }}</h4>
                      <small class="text-muted">Total</small>
                    </div>
                  </div>
                </div>
                <div class="col-4">
                  <div class="card border-0" style="background: #f0fdf4;">
                    <div class="card-body py-2">
                      <h4 class="mb-0 text-success">{{ doctorStats.completed_appointments || 0 }}</h4>
                      <small class="text-muted">Completed</small>
                    </div>
                  </div>
                </div>
                <div class="col-4">
                  <div class="card border-0" style="background: #fef3c7;">
                    <div class="card-body py-2">
                      <h4 class="mb-0" style="color: #d97706;">{{ doctorStats.booked_appointments || 0 }}</h4>
                      <small class="text-muted">Booked</small>
                    </div>
                  </div>
                </div>
                <div class="col-6">
                  <div class="card border-0" style="background: #fee2e2;">
                    <div class="card-body py-2">
                      <h4 class="mb-0 text-danger">{{ doctorStats.cancelled_appointments || 0 }}</h4>
                      <small class="text-muted">Cancelled</small>
                    </div>
                  </div>
                </div>
                <div class="col-6">
                  <div class="card border-0" style="background: #e0f2fe;">
                    <div class="card-body py-2">
                      <h4 class="mb-0 text-info">{{ doctorStats.unique_patients || 0 }}</h4>
                      <small class="text-muted">Patients</small>
                    </div>
                  </div>
                </div>
              </div>
              
              <table class="table table-sm">
                <tr><th>Email</th><td>{{ viewingDoctor?.user?.email || 'N/A' }}</td></tr>
                <tr><th>Phone</th><td>{{ viewingDoctor?.phone || 'N/A' }}</td></tr>
                <tr><th>Department</th><td>{{ viewingDoctor?.department?.name || 'N/A' }}</td></tr>
                <tr><th>Qualification</th><td>{{ viewingDoctor?.qualification || 'N/A' }}</td></tr>
                <tr><th>Experience</th><td>{{ viewingDoctor?.experience_years || 0 }} years</td></tr>
                <tr><th>Consultation Fee</th><td>₹{{ viewingDoctor?.consultation_fee || 0 }}</td></tr>
              </table>
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
