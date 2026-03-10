<script>
import { useUserStore } from "@/stores/user";
import { useRouter } from "vue-router";

export default {
  setup() {
    const userStore = useUserStore();
    const router = useRouter();

    const logout = () => {
      userStore.logout();
      router.push("/");
    };

    return { userStore, logout };
  },
};
</script>

<template>
  <nav class="navbar navbar-expand-lg navbar-dark bg-primary py-2">
    <div class="container">
      <span class="navbar-brand d-flex align-items-center" style="cursor: default;">
        <span class="bg-white text-primary rounded-2 d-flex align-items-center justify-content-center me-2" style="width: 32px; height: 32px;">
          <i class="bi bi-plus-lg" style="font-size: 1.25rem;"></i>
        </span>
        MediCare
      </span>

      <button
        class="navbar-toggler"
        type="button"
        data-bs-toggle="collapse"
        data-bs-target="#navbarNav"
      >
        <span class="navbar-toggler-icon"></span>
      </button>

      <div class="collapse navbar-collapse" id="navbarNav">
        <ul class="navbar-nav me-auto">
          <!-- Home link for non-authenticated users -->
          <li class="nav-item" v-if="!userStore.isAuthenticated">
            <router-link class="nav-link" to="/">Home</router-link>
          </li>

          <!-- Admin Links -->
          <template v-if="userStore.isAdmin">
            <li class="nav-item">
              <router-link class="nav-link" to="/admin/dashboard">Dashboard</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/admin/departments">Departments</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/admin/doctors">Doctors</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/admin/patients">Patients</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/admin/appointments">Appointments</router-link>
            </li>
          </template>

          <!-- Doctor Links -->
          <template v-if="userStore.isDoctor">
            <li class="nav-item">
              <router-link class="nav-link" to="/doctor/dashboard">Dashboard</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/doctor/appointments">All Appointments</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/doctor/patients">My Patients</router-link>
            </li>
          </template>

          <!-- Patient Links -->
          <template v-if="userStore.isPatient">
            <li class="nav-item">
              <router-link class="nav-link" to="/patient/dashboard">Dashboard</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/patient/doctors">Find Doctors</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/patient/appointments">Appointments</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/patient/history">Medical History</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/patient/profile">My Profile</router-link>
            </li>
          </template>
        </ul>

        <ul class="navbar-nav">
          <template v-if="userStore.isAuthenticated">
            <li class="nav-item d-flex align-items-center">
              <span class="text-light opacity-75 me-3" style="font-size: 0.875rem;">
                {{ userStore.user?.name }}
              </span>
              <button class="btn btn-light btn-sm" @click="logout">
                Logout
              </button>
            </li>
          </template>
        </ul>
      </div>
    </div>
  </nav>
</template>
