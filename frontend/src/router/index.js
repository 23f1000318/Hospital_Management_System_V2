import { createRouter, createWebHistory } from "vue-router";
import HomePage from "@/pages/HomePage.vue";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: "/", component: HomePage },
    { path: "/login", component: () => import("@/pages/LoginPage.vue") },
    { path: "/signup", component: () => import("@/pages/SignupPage.vue") },
    
    // Admin routes
    {
      path: "/admin/dashboard",
      component: () => import("@/pages/admin/DashboardAdminPage.vue"),
    },
    {
      path: "/admin/doctors",
      component: () => import("@/pages/admin/DoctorsAdminPage.vue"),
    },
    {
      path: "/admin/patients",
      component: () => import("@/pages/admin/PatientsAdminPage.vue"),
    },
    {
      path: "/admin/appointments",
      component: () => import("@/pages/admin/AppointmentsAdminPage.vue"),
    },
    {
      path: "/admin/departments",
      component: () => import("@/pages/admin/DepartmentsAdminPage.vue"),
    },
    
    // Doctor routes
    {
      path: "/doctor/dashboard",
      component: () => import("@/pages/doctor/DashboardDoctorPage.vue"),
    },
    {
      path: "/doctor/appointments",
      component: () => import("@/pages/doctor/AppointmentsDoctorPage.vue"),
    },
    {
      path: "/doctor/patients",
      component: () => import("@/pages/doctor/PatientsDoctorPage.vue"),
    },
    
    // Patient routes
    {
      path: "/patient/dashboard",
      component: () => import("@/pages/patient/DashboardPatientPage.vue"),
    },
    {
      path: "/patient/profile",
      component: () => import("@/pages/patient/ProfilePatientPage.vue"),
    },
    {
      path: "/patient/doctors",
      component: () => import("@/pages/patient/DoctorsPatientPage.vue"),
    },
    {
      path: "/patient/appointments",
      component: () => import("@/pages/patient/AppointmentsPatientPage.vue"),
    },
    {
      path: "/patient/history",
      component: () => import("@/pages/patient/HistoryPatientPage.vue"),
    },
  ],
});

export default router;
