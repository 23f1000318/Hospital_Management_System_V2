<script>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useUserStore } from "@/stores/user";

export default {
  setup() {
    const router = useRouter();
    const userStore = useUserStore();

    const email = ref("");
    const password = ref("");
    const error = ref("");
    const loading = ref(false);

    const login = async () => {
      error.value = "";
      loading.value = true;

      try {
        await userStore.loginWithCredentials({
          email: email.value,
          password: password.value,
        });

        // Redirect based on role
        const role = userStore.role;
        if (role === "admin") {
          router.push("/admin/dashboard");
        } else if (role === "doctor") {
          router.push("/doctor/appointments");
        } else if (role === "patient") {
          router.push("/patient/doctors");
        } else {
          router.push("/");
        }
      } catch (e) {
        error.value = e.message || "Login failed";
      } finally {
        loading.value = false;
      }
    };

    return { email, password, error, loading, login };
  },
};
</script>

<template>
  <div class="min-vh-100 d-flex align-items-center" style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);">
    <div class="container py-5">
      <div class="row justify-content-center">
        <div class="col-md-5 col-lg-4">
          <div class="text-center mb-4">
            <div class="bg-primary text-white rounded-3 d-inline-flex align-items-center justify-content-center mb-3" style="width: 56px; height: 56px;">
              <i class="bi bi-plus-lg" style="font-size: 2rem;"></i>
            </div>
            <h4 class="fw-semibold mb-1">Welcome back</h4>
            <p class="text-muted" style="font-size: 0.9375rem;">Sign in to your account</p>
          </div>

          <div class="card border-0 shadow-sm">
            <div class="card-body p-4">
              <div v-if="error" class="alert alert-danger py-2" style="font-size: 0.875rem;">{{ error }}</div>

              <form @submit.prevent="login">
                <div class="mb-3">
                  <label class="form-label">Email</label>
                  <input v-model="email" type="email" class="form-control" required placeholder="you@example.com">
                </div>

                <div class="mb-4">
                  <label class="form-label">Password</label>
                  <input v-model="password" type="password" class="form-control" required placeholder="••••••••">
                </div>

                <button type="submit" class="btn btn-primary w-100" :disabled="loading">
                  <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
                  {{ loading ? 'Signing in...' : 'Sign In' }}
                </button>
              </form>
            </div>
          </div>

          <p class="text-center mt-3 mb-0 text-muted" style="font-size: 0.9375rem;">
            New here? <router-link to="/signup" class="text-decoration-none">Create an account</router-link>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
