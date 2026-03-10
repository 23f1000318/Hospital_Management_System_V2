<script>
import { ref, onMounted } from "vue";
import api from "@/utils/api";
import { useUserStore } from "@/stores/user";

export default {
  setup() {
    const userStore = useUserStore();
    const profile = ref(null);
    const loading = ref(true);
    const saving = ref(false);
    const error = ref("");
    const successMsg = ref("");
    
    const editMode = ref(false);
    const form = ref({
      name: "",
      phone: "",
      address: "",
      gender: "",
      blood_group: "",
      date_of_birth: "",
      emergency_contact: "",
    });

    const bloodGroups = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"];
    const genders = ["Male", "Female", "Other"];

    const fetchProfile = async () => {
      try {
        profile.value = await api.get("/patient/profile");
        populateForm();
      } catch (e) {
        error.value = e.message;
      } finally {
        loading.value = false;
      }
    };

    const populateForm = () => {
      if (profile.value) {
        form.value = {
          name: profile.value.user?.name || "",
          phone: profile.value.phone || "",
          address: profile.value.address || "",
          gender: profile.value.gender || "",
          blood_group: profile.value.blood_group || "",
          date_of_birth: profile.value.date_of_birth || "",
          emergency_contact: profile.value.emergency_contact || "",
        };
      }
    };

    const saveProfile = async () => {
      saving.value = true;
      error.value = "";
      try {
        const result = await api.put("/patient/profile", form.value);
        profile.value = result.patient;
        
        // Update user name in store if changed
        if (form.value.name && userStore.user) {
          userStore.setUser({ ...userStore.user, name: form.value.name });
        }
        
        successMsg.value = "Profile updated successfully!";
        setTimeout(() => successMsg.value = "", 3000);
        editMode.value = false;
      } catch (e) {
        error.value = e.message;
      } finally {
        saving.value = false;
      }
    };

    const cancelEdit = () => {
      populateForm();
      editMode.value = false;
    };

    onMounted(fetchProfile);

    return {
      profile, loading, saving, error, successMsg,
      editMode, form, bloodGroups, genders,
      saveProfile, cancelEdit
    };
  },
};
</script>

<template>
  <div class="container py-4">
    <div class="row justify-content-center">
      <div class="col-lg-8">
        <div class="d-flex justify-content-between align-items-center mb-4">
          <h2><i class="bi bi-person-gear me-2"></i>My Profile</h2>
          <router-link to="/patient/dashboard" class="btn btn-outline-secondary">
            <i class="bi bi-arrow-left me-1"></i>Back to Dashboard
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

        <div class="card" v-if="profile && !loading">
          <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
            <span><i class="bi bi-person-badge me-2"></i>Profile Information</span>
            <button v-if="!editMode" class="btn btn-light btn-sm" @click="editMode = true">
              <i class="bi bi-pencil me-1"></i>Edit
            </button>
          </div>
          
          <div class="card-body">
            <!-- View Mode -->
            <div v-if="!editMode">
              <div class="row mb-3">
                <div class="col-md-6">
                  <label class="form-label text-muted">Full Name</label>
                  <p class="fw-bold">{{ profile.user?.name || "N/A" }}</p>
                </div>
                <div class="col-md-6">
                  <label class="form-label text-muted">Email</label>
                  <p class="fw-bold">{{ profile.user?.email || "N/A" }}</p>
                </div>
              </div>
              
              <div class="row mb-3">
                <div class="col-md-6">
                  <label class="form-label text-muted">Phone</label>
                  <p class="fw-bold">{{ profile.phone || "Not set" }}</p>
                </div>
                <div class="col-md-6">
                  <label class="form-label text-muted">Emergency Contact</label>
                  <p class="fw-bold">{{ profile.emergency_contact || "Not set" }}</p>
                </div>
              </div>
              
              <div class="row mb-3">
                <div class="col-md-4">
                  <label class="form-label text-muted">Date of Birth</label>
                  <p class="fw-bold">{{ profile.date_of_birth || "Not set" }}</p>
                </div>
                <div class="col-md-4">
                  <label class="form-label text-muted">Gender</label>
                  <p class="fw-bold">{{ profile.gender || "Not set" }}</p>
                </div>
                <div class="col-md-4">
                  <label class="form-label text-muted">Blood Group</label>
                  <p class="fw-bold">{{ profile.blood_group || "Not set" }}</p>
                </div>
              </div>
              
              <div class="mb-3">
                <label class="form-label text-muted">Address</label>
                <p class="fw-bold">{{ profile.address || "Not set" }}</p>
              </div>
            </div>

            <!-- Edit Mode -->
            <form v-else @submit.prevent="saveProfile">
              <div class="row mb-3">
                <div class="col-md-6">
                  <label class="form-label">Full Name</label>
                  <input type="text" class="form-control" v-model="form.name" required>
                </div>
                <div class="col-md-6">
                  <label class="form-label">Email</label>
                  <input type="email" class="form-control" :value="profile.user?.email" disabled>
                  <small class="text-muted">Email cannot be changed</small>
                </div>
              </div>
              
              <div class="row mb-3">
                <div class="col-md-6">
                  <label class="form-label">Phone</label>
                  <input type="tel" class="form-control" v-model="form.phone" placeholder="Enter phone number">
                </div>
                <div class="col-md-6">
                  <label class="form-label">Emergency Contact</label>
                  <input type="tel" class="form-control" v-model="form.emergency_contact" placeholder="Emergency contact number">
                </div>
              </div>
              
              <div class="row mb-3">
                <div class="col-md-4">
                  <label class="form-label">Date of Birth</label>
                  <input type="date" class="form-control" v-model="form.date_of_birth">
                </div>
                <div class="col-md-4">
                  <label class="form-label">Gender</label>
                  <select class="form-select" v-model="form.gender">
                    <option value="">Select gender</option>
                    <option v-for="g in genders" :key="g" :value="g">{{ g }}</option>
                  </select>
                </div>
                <div class="col-md-4">
                  <label class="form-label">Blood Group</label>
                  <select class="form-select" v-model="form.blood_group">
                    <option value="">Select blood group</option>
                    <option v-for="bg in bloodGroups" :key="bg" :value="bg">{{ bg }}</option>
                  </select>
                </div>
              </div>
              
              <div class="mb-3">
                <label class="form-label">Address</label>
                <textarea class="form-control" v-model="form.address" rows="2" placeholder="Enter your address"></textarea>
              </div>

              <div class="d-flex gap-2">
                <button type="submit" class="btn btn-primary" :disabled="saving">
                  <span v-if="saving" class="spinner-border spinner-border-sm me-1"></span>
                  Save Changes
                </button>
                <button type="button" class="btn btn-secondary" @click="cancelEdit">Cancel</button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
