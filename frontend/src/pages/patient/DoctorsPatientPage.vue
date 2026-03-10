<script>
import { ref, onMounted, computed } from "vue";
import api from "@/utils/api";
import { useRoute } from "vue-router";

export default {
  setup() {
    const formatLocalDate = (dateObj) => {
      const y = dateObj.getFullYear();
      const m = String(dateObj.getMonth() + 1).padStart(2, "0");
      const d = String(dateObj.getDate()).padStart(2, "0");
      return `${y}-${m}-${d}`;
    };

    const route = useRoute();
    const doctors = ref([]);
    const departments = ref([]);
    const loading = ref(true);
    const error = ref("");
    const successMsg = ref("");
    const searchQuery = ref("");
    const selectedDepartment = ref("");
    
    // Booking modal
    const showBookingModal = ref(false);
    const selectedDoctor = ref(null);
    const doctorAvailability = ref({});
    const loadingAvailability = ref(false);
    const bookingLoading = ref(false);
    const bookingForm = ref({
      date: "",
      time: "",
      reason: "",
    });
    
    // Doctor profile modal
    const showProfileModal = ref(false);
    const viewingDoctor = ref(null);

    // Generate next 7 days
    const next7Days = computed(() => {
      const days = [];
      const today = new Date();
      for (let i = 0; i < 7; i++) {
        const date = new Date(today);
        date.setDate(today.getDate() + i);
        const dateStr = formatLocalDate(date);
        const dayName = date.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });
        days.push({ date: dateStr, label: dayName });
      }
      return days;
    });

    const availableSlots = computed(() => {
      if (!bookingForm.value.date || !doctorAvailability.value) return [];
      return doctorAvailability.value[bookingForm.value.date] || [];
    });

    const fetchData = async () => {
      try {
        const [doctorsList, deptList] = await Promise.all([
          api.get("/doctors"),
          api.get("/departments"),
        ]);
        doctors.value = doctorsList;
        departments.value = deptList;
        
        // Check if a specific doctor was requested
        const doctorId = route.query.doctor;
        if (doctorId) {
          const doc = doctors.value.find(d => d.id == doctorId);
          if (doc) {
            openBookingModal(doc);
          }
        }
      } catch (e) {
        error.value = e.message;
      } finally {
        loading.value = false;
      }
    };

    const filteredDoctors = computed(() => {
      return doctors.value.filter((doc) => {
        // Hide blacklisted/inactive doctors
        if (!doc.user?.active) return false;
        
        const matchesSearch =
          !searchQuery.value ||
          doc.user?.name?.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
          doc.qualification?.toLowerCase().includes(searchQuery.value.toLowerCase());
        const matchesDept =
          !selectedDepartment.value ||
          doc.department_id === parseInt(selectedDepartment.value);
        return matchesSearch && matchesDept;
      });
    });

    const viewProfile = (doctor) => {
      viewingDoctor.value = doctor;
      showProfileModal.value = true;
    };

    const openBookingModal = async (doctor) => {
      selectedDoctor.value = doctor;
      bookingForm.value = { date: "", time: "", reason: "" };
      showBookingModal.value = true;
      
      // Fetch doctor's availability
      loadingAvailability.value = true;
      try {
        const res = await api.get(`/doctors/${doctor.id}/availability`);
        doctorAvailability.value = res.availability || {};
      } catch (e) {
        // If no availability set, use empty object
        doctorAvailability.value = {};
      } finally {
        loadingAvailability.value = false;
      }
    };

    const selectDate = (date) => {
      bookingForm.value.date = date;
      bookingForm.value.time = ""; // Reset time when date changes
    };

    const selectTime = (time) => {
      bookingForm.value.time = time;
    };

    const bookAppointment = async () => {
      if (!bookingForm.value.date || !bookingForm.value.time) {
        error.value = "Please select date and time";
        return;
      }
      
      bookingLoading.value = true;
      error.value = "";
      try {
        await api.post("/patient/book-appointment", {
          doctor_id: selectedDoctor.value.id,
          date: bookingForm.value.date,
          time: bookingForm.value.time,
          reason: bookingForm.value.reason,
        });
        showBookingModal.value = false;
        successMsg.value = "Appointment booked successfully!";
        setTimeout(() => successMsg.value = "", 3000);
      } catch (e) {
        error.value = e.message;
      } finally {
        bookingLoading.value = false;
      }
    };

    const hasAvailability = (date) => {
      return doctorAvailability.value[date]?.length > 0;
    };

    onMounted(fetchData);

    return {
      doctors, departments, loading, error, successMsg,
      searchQuery, selectedDepartment, filteredDoctors,
      showBookingModal, selectedDoctor, doctorAvailability,
      loadingAvailability, bookingLoading, bookingForm,
      showProfileModal, viewingDoctor,
      next7Days, availableSlots,
      viewProfile, openBookingModal, selectDate, selectTime,
      bookAppointment, hasAvailability,
    };
  },
};
</script>

<template>
  <div class="container py-4">
    <h2 class="mb-4"><i class="bi bi-search me-2"></i>Find Doctors</h2>

    <!-- Search and Filter -->
    <div class="card mb-4">
      <div class="card-body">
        <div class="row g-3">
          <div class="col-md-6">
            <div class="input-group">
              <span class="input-group-text"><i class="bi bi-search"></i></span>
              <input v-model="searchQuery" type="search" class="form-control" placeholder="Search by doctor name or qualification...">
            </div>
          </div>
          <div class="col-md-4">
            <select v-model="selectedDepartment" class="form-select">
              <option value="">All Departments</option>
              <option v-for="dept in departments" :key="dept.id" :value="dept.id">
                {{ dept.name }}
              </option>
            </select>
          </div>
          <div class="col-md-2">
            <button class="btn btn-outline-secondary w-100" @click="searchQuery = ''; selectedDepartment = ''">
              <i class="bi bi-x-circle me-1"></i>Clear
            </button>
          </div>
        </div>
      </div>
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

    <!-- Doctors Grid -->
    <div class="row g-3" v-if="!loading">
      <div v-for="doc in filteredDoctors" :key="doc.id" class="col-md-6 col-lg-4">
        <div class="card h-100 shadow-sm">
          <div class="card-body">
            <h5 class="card-title">
              <i class="bi bi-person-badge me-2 text-primary"></i>
              {{ doc.user?.name || "Unknown" }}
            </h5>
            <p class="text-muted mb-2">
              <i class="bi bi-building me-1"></i>{{ doc.department?.name || "General" }}
            </p>
            <ul class="list-unstyled small mb-3">
              <li><i class="bi bi-mortarboard me-1"></i><strong>Qualification:</strong> {{ doc.qualification || "N/A" }}</li>
              <li><i class="bi bi-clock me-1"></i><strong>Experience:</strong> {{ doc.experience_years || 0 }} years</li>
              <li><i class="bi bi-currency-rupee me-1"></i><strong>Fee:</strong> ₹{{ doc.consultation_fee || 0 }}</li>
            </ul>
            <div class="d-flex gap-2">
              <button class="btn btn-outline-info btn-sm flex-grow-1" @click="viewProfile(doc)">
                <i class="bi bi-person me-1"></i>Profile
              </button>
              <button class="btn btn-primary btn-sm flex-grow-1" @click="openBookingModal(doc)">
                <i class="bi bi-calendar-plus me-1"></i>Book
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <div v-if="filteredDoctors.length === 0" class="col-12">
        <div class="alert alert-info text-center">
          <i class="bi bi-info-circle me-2"></i>No doctors found matching your criteria.
        </div>
      </div>
    </div>

    <!-- Doctor Profile Modal -->
    <div v-if="showProfileModal" class="modal d-block" style="background: rgba(0,0,0,0.5)">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">
              <i class="bi bi-person-badge me-2"></i>Doctor Profile
            </h5>
            <button type="button" class="btn-close" @click="showProfileModal = false"></button>
          </div>
          <div class="modal-body">
            <div class="row">
              <div class="col-md-4 text-center mb-3">
                <div class="bg-light rounded-circle d-inline-flex align-items-center justify-content-center" style="width: 120px; height: 120px;">
                  <i class="bi bi-person-fill text-secondary" style="font-size: 3rem;"></i>
                </div>
                <h4 class="mt-3">{{ viewingDoctor?.user?.name }}</h4>
                <span class="badge bg-primary">{{ viewingDoctor?.department?.name || 'General' }}</span>
              </div>
              <div class="col-md-8">
                <table class="table table-borderless">
                  <tr>
                    <th width="40%">Qualification</th>
                    <td>{{ viewingDoctor?.qualification || 'N/A' }}</td>
                  </tr>
                  <tr>
                    <th>Experience</th>
                    <td>{{ viewingDoctor?.experience_years || 0 }} years</td>
                  </tr>
                  <tr>
                    <th>Consultation Fee</th>
                    <td>₹{{ viewingDoctor?.consultation_fee || 0 }}</td>
                  </tr>
                  <tr>
                    <th>Contact</th>
                    <td>{{ viewingDoctor?.phone || 'N/A' }}</td>
                  </tr>
                  <tr>
                    <th>Email</th>
                    <td>{{ viewingDoctor?.user?.email || 'N/A' }}</td>
                  </tr>
                </table>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="showProfileModal = false">Close</button>
            <button class="btn btn-primary" @click="showProfileModal = false; openBookingModal(viewingDoctor)">
              <i class="bi bi-calendar-plus me-1"></i>Book Appointment
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Booking Modal -->
    <div v-if="showBookingModal" class="modal d-block" style="background: rgba(0,0,0,0.5)">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">
              <i class="bi bi-calendar-plus me-2"></i>Book Appointment with {{ selectedDoctor?.user?.name }}
            </h5>
            <button type="button" class="btn-close" @click="showBookingModal = false"></button>
          </div>
          <div class="modal-body">
            <div class="alert alert-info">
              <i class="bi bi-info-circle me-2"></i>
              <strong>{{ selectedDoctor?.department?.name }}</strong> | Fee: ₹{{ selectedDoctor?.consultation_fee || 0 }}
            </div>
            
            <!-- Loading -->
            <div v-if="loadingAvailability" class="text-center py-4">
              <div class="spinner-border text-primary"></div>
              <p class="mt-2">Loading availability...</p>
            </div>
            
            <div v-else>
              <!-- Date Selection -->
              <div class="mb-4">
                <label class="form-label fw-bold">Select Date (Next 7 Days)</label>
                <div class="d-flex flex-wrap gap-2">
                  <button 
                    v-for="day in next7Days" 
                    :key="day.date"
                    class="btn"
                    :class="bookingForm.date === day.date ? 'btn-primary' : (hasAvailability(day.date) ? 'btn-outline-primary' : 'btn-outline-secondary')"
                    :disabled="!hasAvailability(day.date)"
                    @click="selectDate(day.date)"
                  >
                    {{ day.label }}
                    <br><small v-if="hasAvailability(day.date)" class="text-success">Available</small>
                    <small v-else class="text-muted">N/A</small>
                  </button>
                </div>
                <small v-if="Object.keys(doctorAvailability).length === 0" class="text-warning">
                  <i class="bi bi-exclamation-triangle me-1"></i>
                  Doctor hasn't set availability. Contact hospital for booking.
                </small>
              </div>
              
              <!-- Time Selection -->
              <div class="mb-4" v-if="bookingForm.date">
                <label class="form-label fw-bold">Select Time</label>
                <div class="d-flex flex-wrap gap-2">
                  <button 
                    v-for="time in availableSlots" 
                    :key="time"
                    class="btn"
                    :class="bookingForm.time === time ? 'btn-success' : 'btn-outline-success'"
                    @click="selectTime(time)"
                  >
                    {{ time }}
                  </button>
                </div>
                <div v-if="availableSlots.length === 0" class="text-muted">
                  No slots available for this date.
                </div>
              </div>
              
              <!-- Reason -->
              <div class="mb-3">
                <label class="form-label fw-bold">Reason for Visit</label>
                <textarea v-model="bookingForm.reason" class="form-control" rows="3" placeholder="Describe your symptoms or reason for visit..."></textarea>
              </div>
              
              <!-- Selected Summary -->
              <div v-if="bookingForm.date && bookingForm.time" class="alert alert-success">
                <i class="bi bi-check-circle me-2"></i>
                <strong>Selected:</strong> {{ bookingForm.date }} at {{ bookingForm.time }}
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="showBookingModal = false">Cancel</button>
            <button 
              class="btn btn-primary" 
              @click="bookAppointment"
              :disabled="!bookingForm.date || !bookingForm.time || bookingLoading"
            >
              <span v-if="bookingLoading" class="spinner-border spinner-border-sm me-1"></span>
              Confirm Booking
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
