<script>
import { ref, onMounted } from "vue";
import api from "@/utils/api";

export default {
  setup() {
    const departments = ref([]);
    const loading = ref(true);
    const error = ref("");
    const showModal = ref(false);
    const editMode = ref(false);
    const form = ref({ name: "", description: "" });

    const fetchDepartments = async () => {
      try {
        departments.value = await api.get("/departments");
      } catch (e) {
        error.value = e.message;
      } finally {
        loading.value = false;
      }
    };

    const openAddModal = () => {
      editMode.value = false;
      form.value = { name: "", description: "" };
      showModal.value = true;
    };

    const openEditModal = (dept) => {
      editMode.value = true;
      form.value = { ...dept };
      showModal.value = true;
    };

    const saveDepartment = async () => {
      try {
        if (editMode.value) {
          await api.patch(`/departments/${form.value.id}`, form.value);
        } else {
          await api.post("/departments", form.value);
        }
        showModal.value = false;
        fetchDepartments();
      } catch (e) {
        error.value = e.message;
      }
    };

    const deleteDepartment = async (id) => {
      if (!confirm("Are you sure you want to delete this department?")) return;
      try {
        await api.delete(`/departments/${id}`);
        fetchDepartments();
      } catch (e) {
        error.value = e.message;
      }
    };

    onMounted(fetchDepartments);

    return {
      departments,
      loading,
      error,
      showModal,
      editMode,
      form,
      openAddModal,
      openEditModal,
      saveDepartment,
      deleteDepartment,
    };
  },
};
</script>

<template>
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2><i class="bi bi-building me-2"></i>Departments</h2>
      <button class="btn btn-primary" @click="openAddModal">
        <i class="bi bi-plus-lg me-1"></i>Add Department
      </button>
    </div>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary"></div>
    </div>

    <div v-if="error" class="alert alert-danger">{{ error }}</div>

    <div class="table-responsive" v-if="!loading">
      <table class="table table-striped">
        <thead>
          <tr>
            <th>ID</th>
            <th>Name</th>
            <th>Description</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="dept in departments" :key="dept.id">
            <td>{{ dept.id }}</td>
            <td>{{ dept.name }}</td>
            <td>{{ dept.description }}</td>
            <td>
              <button class="btn btn-sm btn-outline-primary me-1" @click="openEditModal(dept)">
                <i class="bi bi-pencil"></i>
              </button>
              <button class="btn btn-sm btn-outline-danger" @click="deleteDepartment(dept.id)">
                <i class="bi bi-trash"></i>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal -->
    <div v-if="showModal" class="modal d-block" style="background: rgba(0,0,0,0.5)">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ editMode ? "Edit" : "Add" }} Department</h5>
            <button type="button" class="btn-close" @click="showModal = false"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <label class="form-label">Name</label>
              <input v-model="form.name" class="form-control" required />
            </div>
            <div class="mb-3">
              <label class="form-label">Description</label>
              <textarea v-model="form.description" class="form-control" rows="3"></textarea>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="showModal = false">Cancel</button>
            <button class="btn btn-primary" @click="saveDepartment">Save</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
