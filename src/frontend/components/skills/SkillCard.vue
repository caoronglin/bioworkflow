<script setup lang="ts">
/**
 * SkillCard Component
 * 
 * A card component for displaying skill information in the marketplace.
 * Features elegant hover effects, skill metadata display, and action buttons.
 */

import { computed } from 'vue'
import type { PropType } from 'vue'

interface Skill {
  id: string
  name: string
  slug: string
  description: string
  category: string
  tags: string[]
  author: {
    name: string
    avatar?: string
  }
  version: string
  icon?: string
  screenshots: string[]
  metrics: {
    downloads: number
    ratings_average: number
    ratings_count: number
  }
  status: string
}

const props = defineProps({
  skill: {
    type: Object as PropType<Skill>,
    required: true
  },
  variant: {
    type: String as PropType<'default' | 'compact' | 'featured'>,
    default: 'default'
  }
})

const emit = defineEmits<{
  install: [skill: Skill]
  view: [skill: Skill]
  favorite: [skill: Skill]
}>()

// Format large numbers
const formatNumber = (num: number): string => {
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`
  return num.toString()
}

// Format rating
const formatRating = (rating: number): string => {
  return rating.toFixed(1)
}

// Get category display name
const categoryDisplayName = computed(() => {
  const category = props.skill.category
  return category.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())
})

// Card classes based on variant
const cardClasses = computed(() => {
  const base = 'skill-card'
  return [
    base,
    `${base}--${props.variant}`,
    props.skill.status === 'featured' && `${base}--featured-status`
  ].filter(Boolean)
})
</script>

<template>
  <article :class="cardClasses">
    <!-- Image/Media Section -->
    <div class="skill-card__media">
      <div class="skill-card__icon-wrapper">
        <img
          v-if="skill.icon"
          :src="skill.icon"
          :alt="skill.name"
          class="skill-card__icon"
        />
        <div v-else class="skill-card__icon-placeholder">
          {{ skill.name.charAt(0).toUpperCase() }}
        </div>
      </div>
      
      <!-- Featured Badge -->
      <div v-if="skill.status === 'featured'" class="skill-card__badge">
        <span class="skill-card__badge-text">Featured</span>
      </div>
      
      <!-- Hover Overlay -->
      <div class="skill-card__overlay">
        <button
          class="skill-card__action-btn skill-card__action-btn--primary"
          @click="emit('install', skill)"
        >
          <svg class="skill-card__action-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Install
        </button>
        <button
          class="skill-card__action-btn skill-card__action-btn--secondary"
          @click="emit('view', skill)"
        >
          View Details
        </button>
      </div>
    </div>
    
    <!-- Content Section -->
    <div class="skill-card__content">
      <!-- Header -->
      <div class="skill-card__header">
        <h3 class="skill-card__title">{{ skill.name }}</h3>
        <span class="skill-card__version">v{{ skill.version }}</span>
      </div>
      
      <!-- Description -->
      <p class="skill-card__description">{{ skill.description }}</p>
      
      <!-- Category & Tags -->
      <div class="skill-card__meta">
        <span class="skill-card__category">{{ categoryDisplayName }}</span>
        <div v-if="skill.tags.length > 0" class="skill-card__tags">
          <span
            v-for="tag in skill.tags.slice(0, 3)"
            :key="tag"
            class="skill-card__tag"
          >
            {{ tag }}
          </span>
        </div>
      </div>
      
      <!-- Stats & Author -->
      <div class="skill-card__footer">
        <div class="skill-card__stats">
          <div class="skill-card__stat">
            <svg class="skill-card__stat-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            <span class="skill-card__stat-value">{{ formatNumber(skill.metrics.downloads) }}</span>
          </div>
          <div class="skill-card__stat">
            <svg class="skill-card__stat-icon skill-card__stat-icon--star" viewBox="0 0 24 24" fill="currentColor">
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
            </svg>
            <span class="skill-card__stat-value">{{ formatRating(skill.metrics.ratings_average) }}</span>
            <span class="skill-card__stat-count">({{ formatNumber(skill.metrics.ratings_count) }})</span>
          </div>
        </div>
        
        <div class="skill-card__author">
          <span class="skill-card__author-name">by {{ skill.author.name }}</span>
        </div>
      </div>
    </div>
  </article>
</template>

<style scoped>
.skill-card {
  --card-bg: white;
  --card-border: var(--color-gray-200);
  --card-radius: var(--radius-xl);
  --card-shadow: var(--shadow-base);
  
  position: relative;
  display: flex;
  flex-direction: column;
  background-color: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: var(--card-radius);
  box-shadow: var(--card-shadow);
  overflow: hidden;
  transition: 
    box-shadow var(--duration-moderate) var(--ease-out),
    transform var(--duration-moderate) var(--ease-out);
}

.skill-card:hover {
  box-shadow: var(--shadow-lg);
  transform: translateY(-4px);
}

/* Media Section */
.skill-card__media {
  position: relative;
  aspect-ratio: 16 / 9;
  background: linear-gradient(135deg, var(--color-primary-50), var(--color-secondary-50));
  overflow: hidden;
}

.skill-card__icon-wrapper {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.skill-card__icon {
  width: 64px;
  height: 64px;
  object-fit: contain;
  filter: drop-shadow(0 4px 6px rgb(0 0 0 / 0.1));
}

.skill-card__icon-placeholder {
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary-500);
  color: white;
  font-size: var(--text-2xl);
  font-weight: 700;
  border-radius: var(--radius-lg);
}

.skill-card__badge {
  position: absolute;
  top: var(--space-3);
  right: var(--space-3);
  padding: var(--space-1) var(--space-2);
  background: linear-gradient(135deg, var(--color-warning-500), var(--color-warning-600));
  color: white;
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
  border-radius: var(--radius-full);
  box-shadow: var(--shadow-sm);
}

.skill-card__overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  background: rgb(15 23 42 / 0.8);
  backdrop-filter: blur(4px);
  opacity: 0;
  transition: opacity var(--duration-moderate) var(--ease-out);
}

.skill-card:hover .skill-card__overlay {
  opacity: 1;
}

.skill-card__action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-2-5) var(--space-5);
  font-size: var(--text-sm);
  font-weight: 500;
  border-radius: var(--radius-lg);
  transition: all var(--duration-fast) var(--ease-out);
  cursor: pointer;
  border: none;
}

.skill-card__action-btn--primary {
  background: var(--color-primary-500);
  color: white;
  box-shadow: var(--shadow-md);
}

.skill-card__action-btn--primary:hover {
  background: var(--color-primary-600);
  transform: translateY(-1px);
  box-shadow: var(--shadow-lg);
}

.skill-card__action-btn--secondary {
  background: white;
  color: var(--color-gray-700);
  border: 1px solid var(--color-gray-300);
}

.skill-card__action-btn--secondary:hover {
  background: var(--color-gray-50);
  border-color: var(--color-gray-400);
}

.skill-card__action-icon {
  width: 16px;
  height: 16px;
}

/* Content Section */
.skill-card__content {
  display: flex;
  flex-direction: column;
  flex: 1;
  padding: var(--space-5);
  gap: var(--space-3);
}

.skill-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-2);
}

.skill-card__title {
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--color-gray-900);
  line-height: var(--leading-tight);
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.skill-card__version {
  flex-shrink: 0;
  font-size: var(--text-xs);
  font-weight: 500;
  color: var(--color-gray-500);
  background: var(--color-gray-100);
  padding: var(--space-0-5) var(--space-2);
  border-radius: var(--radius-full);
}

.skill-card__description {
  font-size: var(--text-sm);
  color: var(--color-gray-600);
  line-height: var(--leading-relaxed);
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.skill-card__meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.skill-card__category {
  font-size: var(--text-xs);
  font-weight: 500;
  color: var(--color-primary-600);
  background: var(--color-primary-50);
  padding: var(--space-0-5) var(--space-2);
  border-radius: var(--radius-full);
  text-transform: capitalize;
}

.skill-card__tags {
  display: flex;
  gap: var(--space-1);
}

.skill-card__tag {
  font-size: var(--text-xs);
  color: var(--color-gray-500);
  background: var(--color-gray-100);
  padding: var(--space-0-5) var(--space-2);
  border-radius: var(--radius-full);
}

.skill-card__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: auto;
  padding-top: var(--space-3);
  border-top: 1px solid var(--color-gray-100);
}

.skill-card__stats {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.skill-card__stat {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--text-xs);
  color: var(--color-gray-500);
}

.skill-card__stat-icon {
  width: 14px;
  height: 14px;
}

.skill-card__stat-icon--star {
  color: var(--color-warning-500);
}

.skill-card__stat-value {
  font-weight: 500;
  color: var(--color-gray-700);
}

.skill-card__stat-count {
  color: var(--color-gray-400);
}

.skill-card__author {
  font-size: var(--text-xs);
  color: var(--color-gray-500);
}

.skill-card__author-name {
  font-weight: 500;
  color: var(--color-gray-600);
}

/* Variant: Compact */
.skill-card--compact .skill-card__media {
  aspect-ratio: 3 / 2;
}

.skill-card--compact .skill-card__content {
  padding: var(--space-4);
}

.skill-card--compact .skill-card__description {
  -webkit-line-clamp: 1;
}

.skill-card--compact .skill-card__footer {
  display: none;
}

/* Variant: Featured */
.skill-card--featured {
  border-color: var(--color-warning-200);
  box-shadow: var(--shadow-md);
}

.skill-card--featured:hover {
  box-shadow: var(--shadow-xl);
}

.skill-card--featured .skill-card__media {
  aspect-ratio: 21 / 9;
}

.skill-card--featured .skill-card__content {
  padding: var(--space-6);
}

.skill-card--featured .skill-card__title {
  font-size: var(--text-xl);
}

/* Responsive */
@media (max-width: 640px) {
  .skill-card__content {
    padding: var(--space-4);
  }
  
  .skill-card__footer {
    flex-direction: column;
    gap: var(--space-3);
    align-items: flex-start;
  }
}
</style>
