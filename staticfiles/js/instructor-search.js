/**
 * Búsqueda en tiempo real para instructores
 * Este script maneja la búsqueda AJAX y la visualización de resultados
 */

document.addEventListener("DOMContentLoaded", () => {
    // Configuración
    const config = {
      useAjaxSearch: true, // Cambiar a false para usar búsqueda del lado del cliente
      minChars: 2, // Mínimo de caracteres para iniciar la búsqueda
      debounceTime: 300, // Tiempo de espera entre pulsaciones de teclas (ms)
      highlightResults: true, // Resaltar coincidencias en los resultados
      searchEndpoint: "/instructores/search/", // URL fija para búsqueda AJAX
      animateResults: true, // Animar resultados al mostrarlos
      showLoadingIndicator: true, // Mostrar indicador de carga durante la búsqueda
    }
  
    // Elementos DOM
    const searchInput = document.getElementById("live-search-input")
    const clearButton = document.getElementById("clear-search-btn")
    const searchButton = document.getElementById("search-btn")
    const searchStatus = document.getElementById("search-status")
    const searchStatusText = document.getElementById("search-status-text")
    const tableBody = document.getElementById("instructors-table-body")
    const tableLoading = document.getElementById("table-loading")
  
    // Si no hay elementos de búsqueda, salir
    if (!searchInput) return
  
    // Almacenar todas las filas originales para búsqueda del lado del cliente
    let allRows = []
    if (!config.useAjaxSearch) {
      allRows = Array.from(tableBody.querySelectorAll('tr:not([id="no-results-row"])'))
    }
  
    // Función para debounce (evitar múltiples llamadas rápidas)
    function debounce(func, wait) {
      let timeout
      return function (...args) {
        clearTimeout(timeout)
        timeout = setTimeout(() => func.apply(this, args), wait)
      }
    }
  
    // Función para resaltar texto coincidente
    function highlightText(text, query) {
      if (!config.highlightResults || !query) return text
  
      const regex = new RegExp(`(${query.replace(/[-/\\^$*+?.()|[\]{}]/g, "\\$&")})`, "gi")
      return text.replace(regex, "<mark>$1</mark>")
    }
  
    // Función para mostrar mensaje de "no hay resultados"
    function showNoResults(query) {
      // Eliminar mensaje existente si hay
      const existingMessage = document.getElementById("no-results-row")
      if (existingMessage) existingMessage.remove()
  
      // Crear y mostrar nuevo mensaje
      const noResults = document.createElement("tr")
      noResults.id = "no-results-row"
      noResults.innerHTML = `
             <td colspan="6" class="text-center">
                 <div class="empty-state" style="padding: 2rem 1rem;">
                     <div class="empty-state-icon" style="font-size: 2rem;">
                         <i class="bi bi-search" aria-hidden="true"></i>
                     </div>
                     <h3 class="empty-state-title">No se encontraron resultados</h3>
                     <p class="empty-state-message">
                         No hay instructores que coincidan con "${query}"
                     </p>
                 </div>
             </td>
         `
      tableBody.appendChild(noResults)
    }
  
    // Función para actualizar el estado de la búsqueda
    function updateSearchStatus(message, isSearching = false, isError = false) {
      if (message) {
        searchStatusText.innerHTML = message
        searchStatus.style.display = "block"
  
        // Actualizar clases según el estado
        searchStatus.classList.remove("searching", "error")
  
        if (isSearching) {
          searchStatus.classList.add("searching")
          searchStatusText.innerHTML = `<i class="bi bi-arrow-repeat spin me-1"></i> ${message}`
        } else if (isError) {
          searchStatus.classList.add("error")
          searchStatusText.innerHTML = `<i class="bi bi-exclamation-triangle me-1"></i> ${message}`
        } else {
          searchStatusText.innerHTML = `<i class="bi bi-info-circle me-1"></i> ${message}`
        }
      } else {
        searchStatus.style.display = "none"
      }
    }
  
    // Función para búsqueda del lado del cliente
    function clientSideSearch(query) {
      query = query.toLowerCase().trim()
  
      // Ocultar todas las filas primero
      let visibleCount = 0
  
      allRows.forEach((row) => {
        let found = false
  
        // Buscar en todas las celdas excepto la última (acciones)
        const cells = row.querySelectorAll("td:not(:last-child)")
        cells.forEach((cell) => {
          const text = cell.textContent.toLowerCase()
          if (text.includes(query)) {
            found = true
  
            // Resaltar coincidencias si está habilitado
            if (config.highlightResults && query.length > 0) {
              const originalHTML = cell.innerHTML
              // Solo resaltar texto, no HTML
              const textNodes = Array.from(cell.childNodes).filter(
                (node) =>
                  node.nodeType === Node.TEXT_NODE || (node.nodeType === Node.ELEMENT_NODE && !node.querySelector("i")),
              )
  
              textNodes.forEach((node) => {
                if (node.nodeType === Node.TEXT_NODE) {
                  const newText = highlightText(node.textContent, query)
                  if (newText !== node.textContent) {
                    const span = document.createElement("span")
                    span.innerHTML = newText
                    node.parentNode.replaceChild(span, node)
                  }
                } else if (node.nodeType === Node.ELEMENT_NODE) {
                  // Para elementos como enlaces, etc.
                  node.innerHTML = highlightText(node.innerHTML, query)
                }
              })
            }
          }
        })
  
        // Mostrar u ocultar la fila según el resultado
        if (found || query === "") {
          row.style.display = ""
          visibleCount++
  
          // Añadir clase para animación
          if (config.animateResults) {
            row.classList.add("animate-row")
            row.style.animationDelay = visibleCount * 0.05 + "s"
          }
        } else {
          row.style.display = "none"
          row.classList.remove("animate-row")
        }
      })
  
      // Mostrar mensaje si no hay resultados
      if (visibleCount === 0 && query !== "") {
        showNoResults(query)
        updateSearchStatus(`No se encontraron resultados para "${query}"`)
      } else if (query !== "") {
        updateSearchStatus(`Se encontraron ${visibleCount} resultados para "${query}"`)
      } else {
        updateSearchStatus("")
      }
  
      return visibleCount
    }
  
    // Función para búsqueda AJAX del lado del servidor
    async function serverSideSearch(query) {
      try {
        // Mostrar indicador de carga
        if (config.showLoadingIndicator && tableLoading) {
          tableLoading.style.display = "flex"
        }
        updateSearchStatus("Buscando...", true)
  
        // Realizar petición AJAX
        const response = await fetch(`${config.searchEndpoint}?q=${encodeURIComponent(query)}`, {
          headers: {
            "X-Requested-With": "XMLHttpRequest",
          },
        })
  
        if (!response.ok) {
          throw new Error(`Error ${response.status}: ${response.statusText}`)
        }
  
        const data = await response.json()
  
        // Limpiar tabla actual
        const existingRows = tableBody.querySelectorAll("tr")
        existingRows.forEach((row) => row.remove())
  
        // Mostrar resultados o mensaje de no resultados
        if (data.results && data.results.length > 0) {
          // Crear filas para cada resultado
          data.results.forEach((instructor, index) => {
            const row = document.createElement("tr")
            if (config.animateResults) {
              row.className = "animate-row"
              row.style.animationDelay = index * 0.05 + "s"
            }
            row.dataset.id = instructor.id
  
            // Crear celdas con datos del instructor
            row.innerHTML = `
                         <td class="text-center">${highlightText(instructor.nombres, query)}</td>
                         <td class="text-center">${highlightText(instructor.apellidos, query)}</td>
                         <td class="text-center">
                             <div class="email-cell justify-content-center">
                                 <i class="bi bi-envelope" aria-hidden="true"></i>
                                 <a href="mailto:${instructor.correo_institucional}" class="email-link">
                                     ${highlightText(instructor.correo_institucional, query)}
                                 </a>
                             </div>
                         </td>
                         <td class="text-center">
                             <div class="phone-cell justify-content-center">
                                 <i class="bi bi-telephone" aria-hidden="true"></i>
                                 ${highlightText(instructor.numero_celular, query)}
                             </div>
                         </td>
                         <td class="text-center">${highlightText(instructor.numero_cedula, query)}</td>
                         <td class="text-center">
                             <div class="action-buttons">
                                 <a href="/instructores/${instructor.id}/edit/" 
                                    class="action-btn edit-btn" 
                                    aria-label="Editar ${instructor.nombres} ${instructor.apellidos}"
                                    data-bs-toggle="tooltip" 
                                    data-bs-title="Editar">
                                     <i class="bi bi-pencil-square" aria-hidden="true"></i>
                                 </a>
                                 <button type="button"
                                         class="action-btn delete-btn delete-instructor" 
                                         data-id="${instructor.id}"
                                         data-nombre="${instructor.nombres} ${instructor.apellidos}"
                                         aria-label="Eliminar ${instructor.nombres} ${instructor.apellidos}"
                                         data-bs-toggle="tooltip" 
                                         data-bs-title="Eliminar">
                                     <i class="bi bi-trash" aria-hidden="true"></i>
                                 </button>
                             </div>
                         </td>
                     `
  
            tableBody.appendChild(row)
          })
  
          // Reinicializar tooltips para los nuevos botones
          if (typeof bootstrap !== "undefined") {
            const newTooltips = tableBody.querySelectorAll('[data-bs-toggle="tooltip"]')
            newTooltips.forEach((el) => {
              const tooltip = new bootstrap.Tooltip(el, {
                delay: { show: 300, hide: 100 },
                placement: "top",
              })
            })
          }
  
          // Reinicializar manejadores de eventos para botones de eliminar
          initDeleteButtons()
  
          // Actualizar información de paginación
          updatePaginationInfo(data.results.length, query)
  
          // Actualizar mensaje de estado
          updateSearchStatus(`Se encontraron ${data.results.length} resultados para "${query}"`)
        } else {
          showNoResults(query)
          updateSearchStatus(`No se encontraron resultados para "${query}"`)
          updatePaginationInfo(0, query)
        }
  
        // Ocultar indicador de carga
        if (config.showLoadingIndicator && tableLoading) {
          tableLoading.style.display = "none"
        }
  
        return data.results ? data.results.length : 0
      } catch (error) {
        console.error("Error en la búsqueda:", error)
        updateSearchStatus(`Error al buscar: ${error.message}`, false, true)
        if (config.showLoadingIndicator && tableLoading) {
          tableLoading.style.display = "none"
        }
        return 0
      }
    }
  
    // Función para inicializar los botones de eliminar
    function initDeleteButtons() {
      const deleteButtons = document.querySelectorAll(".delete-instructor")
      deleteButtons.forEach((button) => {
        // Evitar duplicar event listeners
        button.removeEventListener("click", handleDeleteClick)
        button.addEventListener("click", handleDeleteClick)
      })
    }
  
    // Manejador para el evento de clic en botón eliminar
    function handleDeleteClick(e) {
      e.preventDefault()
  
      // Ocultar cualquier tooltip
      if (typeof bootstrap !== "undefined") {
        const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
        tooltipTriggerList.forEach((tooltipTriggerEl) => {
          const tooltip = bootstrap.Tooltip.getInstance(tooltipTriggerEl)
          if (tooltip) tooltip.hide()
        })
      }
  
      const instructorId = this.getAttribute("data-id")
      const instructorNombre = this.getAttribute("data-nombre")
  
      if (typeof Swal !== "undefined") {
        Swal.fire({
          title: "¿Estás seguro?",
          html: "¿Deseas eliminar al instructor <strong>" + instructorNombre + "</strong>?",
          icon: "warning",
          showCancelButton: true,
          confirmButtonColor: "#28a745",
          cancelButtonColor: "#6c757d",
          confirmButtonText: "Sí, eliminar",
          cancelButtonText: "Cancelar",
          reverseButtons: true,
          showLoaderOnConfirm: true,
          focusConfirm: false,
          allowOutsideClick: () => !Swal.isLoading(),
          preConfirm: () =>
            new Promise((resolve) => {
              // Mostrar indicador de carga
              document.body.classList.add("processing")
  
              const form = document.createElement("form")
              form.method = "POST"
              form.action = "/instructores/" + instructorId + "/delete/"
  
              const csrf = document.createElement("input")
              csrf.type = "hidden"
              csrf.name = "csrfmiddlewaretoken"
              csrf.value = document.querySelector("[name=csrfmiddlewaretoken]").value
  
              form.appendChild(csrf)
              document.body.appendChild(form)
              form.submit()
            }),
        })
      } else {
        // Fallback si SweetAlert no está disponible
        if (confirm(`¿Estás seguro de que deseas eliminar al instructor ${instructorNombre}?`)) {
          const form = document.createElement("form")
          form.method = "POST"
          form.action = "/instructores/" + instructorId + "/delete/"
  
          const csrf = document.createElement("input")
          csrf.type = "hidden"
          csrf.name = "csrfmiddlewaretoken"
          csrf.value = document.querySelector("[name=csrfmiddlewaretoken]").value
  
          form.appendChild(csrf)
          document.body.appendChild(form)
          form.submit()
        }
      }
    }
  
    // Función para actualizar la información de paginación
    function updatePaginationInfo(count, query) {
      const totalCountElement = document.getElementById("total-count")
      const totalItemsElement = document.getElementById("total-items")
      const startIndexElement = document.getElementById("start-index")
      const endIndexElement = document.getElementById("end-index")
      const searchTermElement = document.getElementById("search-term")
      const paginationContainer = document.querySelector(".pagination-container")
  
      if (totalCountElement) totalCountElement.textContent = count
      if (totalItemsElement) totalItemsElement.textContent = count
  
      if (startIndexElement && endIndexElement) {
        if (count > 0) {
          startIndexElement.textContent = "1"
          endIndexElement.textContent = count
        } else {
          startIndexElement.textContent = "0"
          endIndexElement.textContent = "0"
        }
      }
  
      if (searchTermElement && query) {
        searchTermElement.textContent = query
      }
  
      // Mostrar u ocultar la paginación según si hay resultados
      if (paginationContainer) {
        paginationContainer.style.display = count > 0 ? "flex" : "none"
      }
  
      // Simplificar la paginación para resultados de búsqueda
      const pagination = document.getElementById("pagination")
      if (pagination && query) {
        // Simplificar a solo "primera página" cuando se está buscando
        pagination.innerHTML = `
                 <li class="page-item">
                     <a class="page-link" href="/instructores/" aria-label="Volver a la lista completa">
                         <i class="bi bi-arrow-left" aria-hidden="true"></i>
                     </a>
                 </li>
             `
      }
    }
  
    // Función principal de búsqueda
    const performSearch = debounce(async () => {
      const query = searchInput.value.trim()
  
      // Actualizar estado del botón de limpiar
      if (clearButton) {
        clearButton.style.display = query ? "flex" : "none"
      }
  
      // Si la consulta está vacía, mostrar todos los instructores
      if (query === "") {
        if (config.useAjaxSearch) {
          // Redirigir a la página principal de instructores sin parámetros
          window.location.href = "/instructores/"
          return
        } else {
          // Para búsqueda del lado del cliente, mostrar todas las filas
          allRows.forEach((row) => {
            row.style.display = ""
            // Eliminar resaltados previos
            row.querySelectorAll("mark").forEach((mark) => {
              const parent = mark.parentNode
              parent.replaceChild(document.createTextNode(mark.textContent), mark)
              parent.normalize() // Unir nodos de texto adyacentes
            })
          })
  
          // Eliminar mensaje de no resultados si existe
          const noResultsRow = document.getElementById("no-results-row")
          if (noResultsRow) noResultsRow.remove()
  
          updateSearchStatus("")
          return
        }
      }
  
      // Si la consulta es muy corta, no realizar búsqueda
      if (query.length < config.minChars) {
        updateSearchStatus(`Ingrese al menos ${config.minChars} caracteres para buscar`)
        return
      }
  
      // Ejecutar búsqueda según configuración
      if (config.useAjaxSearch) {
        await serverSideSearch(query)
      } else {
        clientSideSearch(query)
      }
    }, config.debounceTime)
  
    // Eventos para la búsqueda
    if (searchInput) {
      // Evento de entrada de texto
      searchInput.addEventListener("input", performSearch)
  
      // Evento de tecla Escape para limpiar
      searchInput.addEventListener("keydown", function (e) {
        if (e.key === "Escape") {
          this.value = ""
          if (clearButton) clearButton.style.display = "none"
          performSearch()
        }
      })
  
      // Evento para el botón de búsqueda
      if (searchButton) {
        searchButton.addEventListener("click", () => {
          performSearch()
        })
      }
  
      // Evento para el botón de limpiar
      if (clearButton) {
        clearButton.addEventListener("click", function () {
          searchInput.value = ""
          this.style.display = "none"
          searchInput.focus()
          performSearch()
        })
      }
  
      // Realizar búsqueda inicial si hay texto
      if (searchInput.value.trim()) {
        performSearch()
      }
    }
  
    // Atajos de teclado
    document.addEventListener("keydown", (e) => {
      // Ctrl/Cmd + K para enfocar el campo de búsqueda
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault()
        if (searchInput) searchInput.focus()
      }
    })
  
    // Inicializar botones de eliminar
    initDeleteButtons()
  
    // Declarar bootstrap y Swal si no están definidos globalmente
    if (typeof bootstrap === "undefined") {
      window.bootstrap = bootstrap
    }
    if (typeof Swal === "undefined") {
      window.Swal = Swal
    }
  })
  