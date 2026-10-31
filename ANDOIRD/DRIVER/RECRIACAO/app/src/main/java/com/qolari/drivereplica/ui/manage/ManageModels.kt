package com.qolari.drivereplica.ui.manage

import com.qolari.drivereplica.data.Blocker
import com.qolari.drivereplica.net.VehiclesResponse

/** Veículo para os ecrãs Veículos e "Os seus veículos" (capturas 080, 082). */
data class VehicleItem(val uuid: String, val title: String, val plate: String, val isDefault: Boolean)

enum class DocStatus { APPROVED, PENDING, REJECTED }

/** Documento do motorista ou do veículo (captura 083): estado, validade e nota de rejeição vindos do backend. */
data class DocumentItem(val key: String, val title: String, val status: DocStatus, val expiresOn: String?, val note: String) {
    val done: Boolean get() = status == DocStatus.APPROVED
}

/** Perfil do Menu (captura 064): nome, avaliação, taxa de aceitação e veículo. */
data class ProfileSummary(
    val name: String,
    val rating: String,
    val acceptance: String,
    val vehicle: String?,
    /** Matrícula, para o bloco "Driver" da folha de itinerário. */
    val plate: String? = null,
    /** Lotação do veículo, para o mesmo bloco. */
    val capacity: String? = null,
)

/** Linha do Centro de segurança / ferramentas (capturas 014, 017). */
data class SafetyRow(val title: String, val subtitle: String)

object ManageMapper {

    /** "2020 Citroën E-C4"; sem ano, só marca e modelo. */
    fun vehicles(resp: VehiclesResponse?): List<VehicleItem> = resp?.vehicles.orEmpty().map { v ->
        val name = listOfNotNull(v.year?.toString(), v.make, v.model).joinToString(" ").ifBlank { v.name.orEmpty() }
        VehicleItem(v.uuid.orEmpty(), name, v.licensePlate.orEmpty(), v.isDefault == true)
    }

    /** Documentos do motorista seguidos dos do veículo, com o estado do backend (pending|approved|rejected). */
    fun documents(resp: com.qolari.drivereplica.net.DocumentsResponse?): List<DocumentItem> =
        (resp?.driverDocuments.orEmpty() + resp?.vehicleDocuments.orEmpty()).map { d ->
            val status = when (d.status) { "approved" -> DocStatus.APPROVED; "rejected" -> DocStatus.REJECTED; else -> DocStatus.PENDING }
            DocumentItem(d.kind.orEmpty(), d.title ?: d.kind.orEmpty(), status, d.expiresOn?.takeIf { it.isNotBlank() }, d.note.orEmpty())
        }

    fun documentsAllDone(items: List<DocumentItem>) = items.all { it.done }

    /** "2029-12-31" -> "31/12/2029"; texto fora do formato passa tal e qual. */
    fun expiry(iso: String?): String? = iso?.let { Regex("""(\d{4})-(\d{2})-(\d{2})""").matchEntire(it)?.let { m -> "${m.groupValues[3]}/${m.groupValues[2]}/${m.groupValues[1]}" } ?: it }

    fun profile(hub: com.qolari.drivereplica.net.ProfileHub?): ProfileSummary? {
        val p = hub?.profile ?: return null
        val rating = p.rating?.let { "%.2f".format(java.util.Locale("pt", "PT"), it) } ?: "--"
        val v = p.vehicle
        return ProfileSummary(
            p.firstName.orEmpty(),
            rating,
            p.acceptanceRate?.let { "$it %" } ?: "-- %",
            p.vehicleLabel,
            plate = v?.get("licensePlate")?.asString?.takeIf { it.isNotBlank() },
            capacity = v?.get("capacity")?.takeIf { it.isJsonPrimitive }?.asInt?.toString(),
        )
    }
}

object SafetyContent {
    /** Ferramentas de segurança (captura 014). Só "Centro de segurança" tem ecrã próprio; as outras abrem uma página informativa. */
    val tools = listOf(
        SafetyRow("Assistência 112", "Para contactar os serviços de emergência."),
        SafetyRow("Acompanhar a minha viagem", "Fique online para começar a partilhar viagens."),
        SafetyRow("Verificação do PIN", "Utilize um código de utilizador para ajudar a recolher a pessoa certa."),
        SafetyRow("Comprovativo do estado da viagem", "Mostrar às autoridades policiais o estado da sua viagem atual."),
        SafetyRow("Centro de segurança", "Consultar as suas definições e os seus recursos de segurança."),
    )

    /** Secções do Centro de segurança (capturas 017, 018, 024). */
    val sections = listOf(
        "Preferências e controlos" to listOf(
            SafetyRow("Verificação do PIN", "Utilize um código de utilizador para ajudar a recolher a pessoa certa."),
            SafetyRow("Gravar a minha viagem", "Utilize o seu telemóvel para gravar as suas viagens."),
            SafetyRow("Acompanhar a minha viagem", "Partilhe facilmente a sua localização e o estado da sua viagem."),
        ),
        "Detalhes da viagem" to listOf(
            SafetyRow("Alertas de limite de velocidade", "Ative as notificações para ajudar a gerir o excesso de velocidade."),
        ),
        "Recursos" to listOf(
            SafetyRow("Sugestões de segurança", "Dicas para conduzir em segurança."),
            SafetyRow("Segurança para o motorista", "Informação de segurança pensada para motoristas."),
        ),
    )
}
