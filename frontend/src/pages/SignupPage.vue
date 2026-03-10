<script>
import { ref } from "vue";
import { useRouter } from "vue-router";
import api from "@/utils/api";

export default {
  setup() {
    const router = useRouter();

    const name = ref("");
    const email = ref("");
    const password = ref("");
    const role = ref("patient");
    const error = ref("");
    const success = ref("");
    const loading = ref(false);

    const register = async () => {
      error.value = "";
      success.value = "";
      loading.value = true;

      try {
        const res = await api.post("/auth/register", {
          name: name.value,
          email: email.value,
          password: password.value,
          role: role.value,
        });

        success.value = res.message || "Registration successful! Redirecting to login...";
        setTimeout(() => router.push("/login"), 2000);
      } catch (e) {
        error.value = e.message || "Registration failed";
      } finally {
        loading.value = false;
      }
    };

    return { name, email, password, role, error, success, loading, register };
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
            <h4 class="fw-semibold mb-1">Create Account</h4>
            <p class="text-muted" style="font-size: 0.9375rem;">Register as a new patient</p>
          </div>

          <div class="card border-0 shadow-sm">
            <div class="card-body p-4">
              <div v-if="error" class="alert alert-danger py-2" style="font-size: 0.875rem;">{{ error }}</div>
              <div v-if="success" class="alert alert-success py-2" style="font-size: 0.875rem;">{{ success }}</div>

              <form @submit.prevent="register">
                <div class="mb-3">
                  <label class="form-label">Full Name</label>
                  <input v-model="name" type="text" class="form-control" required placeholder="John Doe">
                </div>

                <div class="mb-3">
                  <label class="form-label">Email</label>
                  <input v-model="email" type="email" class="form-control" required placeholder="you@example.com">
                </div>

                <div class="mb-4">
                  <label class="form-label">Password</label>
                  <input v-model="password" type="password" class="form-control" required placeholder="Create a password">
                </div>

                <input type="hidden" v-model="role" />

                <button type="submit" class="btn btn-primary w-100" :disabled="loading">
                  <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
                  {{ loading ? 'Creating...' : 'Create Account' }}
                </button>
              </form>
            </div>
          </div>

          <p class="text-center mt-3 mb-0 text-muted" style="font-size: 0.9375rem;">
            Already have an account? <router-link to="/login" class="text-decoration-none">Sign in</router-link>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
