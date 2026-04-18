"""
Entity Extraction Service for Engels Project
Extracts entities and relations from text using LLM (Ollama)
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field
from enum import Enum
import json
import httpx
from .config import settings


class EntityType(str, Enum):
    """Marxist ontology entity types"""
    CLASS = "класс"
    EPOCH = "эпоха"
    MODE_OF_PRODUCTION = "тип_производства"
    PERSON = "персона"
    INSTITUTION = "институт"
    CONCEPT = "понятие"
    EVENT = "событие"
    LOCATION = "локация"


class RelationType(str, Enum):
    """Relation types between entities"""
    BELONGS_TO = "принадлежит_к"  # class belongs to epoch
    ACTS_IN = "действует_в"  # person acts in epoch
    PRODUCES = "производит"  # mode of production produces goods
    EXPLOITS = "эксплуатирует"  # class exploits another class
    CONTRADICTS = "противоречит"  # concept contradicts another
    LEADS_TO = "приводит_к"  # event leads to another
    LOCATED_IN = "расположен_в"  # location within another
    PARTICIPATES_IN = "участвует_в"  # person participates in event
    OWNS = "владеет"  # class owns means of production
    CREATED_BY = "создан"  # concept created by person


class Entity(BaseModel):
    """Extracted entity from text"""
    id: Optional[str] = None
    name: str = Field(..., description="Name of the entity")
    entity_type: EntityType = Field(..., description="Type of entity")
    description: Optional[str] = Field(None, description="Description of the entity")
    mentions: List[str] = Field(default_factory=list, description="All mentions in text")
    confidence: float = Field(0.9, ge=0.0, le=1.0, description="Confidence score")
    needs_review: bool = Field(False, description="Flag for manual review")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Relation(BaseModel):
    """Relation between two entities"""
    id: Optional[str] = None
    source_entity: str = Field(..., description="Source entity name")
    target_entity: str = Field(..., description="Target entity name")
    relation_type: RelationType = Field(..., description="Type of relation")
    description: Optional[str] = Field(None, description="Description of relation")
    confidence: float = Field(0.9, ge=0.0, le=1.0, description="Confidence score")
    needs_review: bool = Field(False, description="Flag for manual review")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExtractionResult(BaseModel):
    """Result of entity and relation extraction"""
    entities: List[Entity] = Field(default_factory=list)
    relations: List[Relation] = Field(default_factory=list)
    text_hash: Optional[str] = None
    processing_time_ms: Optional[float] = None


class PIIData(BaseModel):
    """Detected PII data"""
    type: str = Field(..., description="Type of PII (email, phone, name, etc.)")
    value: str = Field(..., description="Detected PII value")
    start_pos: int = Field(..., description="Start position in text")
    end_pos: int = Field(..., description="End position in text")
    replacement: str = Field(..., description="Anonymized replacement")


class EntityExtractor:
    """Service for extracting entities and relations from text using LLM"""
    
    def __init__(self):
        self.ollama_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.timeout = 60.0
        
        # PII patterns
        self.pii_patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}\b',
            'ip_address': r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
            'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
        }
    
    async def extract_entities_and_relations(
        self, 
        text: str, 
        chunk_id: Optional[str] = None
    ) -> ExtractionResult:
        """
        Extract entities and relations from text using LLM
        
        Args:
            text: Input text to analyze
            chunk_id: Optional ID of the text chunk
            
        Returns:
            ExtractionResult with entities and relations
        """
        import time
        start_time = time.time()
        
        # First, anonymize PII data
        anonymized_text, pii_data = self.anonymize_pii(text)
        
        # Prepare prompt for LLM
        prompt = self._build_extraction_prompt(anonymized_text)
        
        try:
            # Call Ollama API
            llm_response = await self._call_ollama(prompt)
            
            # Parse response
            entities, relations = self._parse_llm_response(llm_response, pii_data)
            
            processing_time = (time.time() - start_time) * 1000
            
            return ExtractionResult(
                entities=entities,
                relations=relations,
                text_hash=chunk_id,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            # Fallback to rule-based extraction if LLM fails
            entities, relations = self._rule_based_extraction(anonymized_text, pii_data)
            
            processing_time = (time.time() - start_time) * 1000
            
            return ExtractionResult(
                entities=entities,
                relations=relations,
                text_hash=chunk_id,
                processing_time_ms=processing_time
            )
    
    def _build_extraction_prompt(self, text: str) -> str:
        """Build prompt for entity and relation extraction"""
        
        system_prompt = """Ты — эксперт по историческому материализму и марксистскому анализу.
Твоя задача — извлечь сущности и связи из текста согласно марксистской онтологии.

Типы сущностей:
- класс: социальный класс (буржуазия, пролетариат, крестьянство и т.д.)
- эпоха: историческая эпоха (феодализм, капитализм, социализм и т.д.)
- тип_производства: способ производства (рабовладельческий, феодальный, капиталистический и т.д.)
- персона: историческая личность
- институт: социальный институт (государство, церковь, профсоюзы и т.д.)
- понятие: теоретическое понятие (прибавочная стоимость, отчуждение и т.д.)
- событие: историческое событие (революция, забастовка и т.д.)
- локация: географическое место

Типы связей:
- принадлежит_к: класс принадлежит эпохе
- действует_в: персона действует в эпохе
- производит: тип производства производит товары
- эксплуатирует: класс эксплуатирует другой класс
- противоречит: понятие противоречит другому понятию
- приводит_к: событие приводит к другому событию
- расположен_в: локация внутри другой локации
- участвует_в: персона участвует в событии
- владеет: класс владеет средствами производства
- создан: понятие создано персоной

Верни ответ ТОЛЬКО в формате JSON:
{
    "entities": [
        {
            "name": "название сущности",
            "entity_type": "тип сущности",
            "description": "краткое описание",
            "mentions": ["упоминание1", "упоминание2"],
            "confidence": 0.95,
            "needs_review": false
        }
    ],
    "relations": [
        {
            "source_entity": "сущность1",
            "target_entity": "сущность2",
            "relation_type": "тип связи",
            "description": "описание связи",
            "confidence": 0.9,
            "needs_review": false
        }
    ]
}

Если не уверен в сущности или связи, установи needs_review: true.
Если текст не содержит сущностей марксистской онтологии, верни пустые списки."""

        user_prompt = f"Проанализируй следующий текст и извлеки сущности и связи:\n\n{text}"
        
        return f"{system_prompt}\n\n{user_prompt}"
    
    async def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API for text analysis"""
        
        url = f"{self.ollama_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9,
            }
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "")
    
    def _parse_llm_response(
        self, 
        response: str, 
        pii_data: List[PIIData]
    ) -> Tuple[List[Entity], List[Relation]]:
        """Parse LLM response into entities and relations"""
        
        entities = []
        relations = []
        
        try:
            # Try to find JSON in response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                # No JSON found, return empty
                return entities, relations
            
            json_str = response[json_start:json_end]
            data = json.loads(json_str)
            
            # Parse entities
            for ent in data.get("entities", []):
                entity = Entity(
                    name=ent.get("name", ""),
                    entity_type=EntityType(ent.get("entity_type", "понятие")),
                    description=ent.get("description"),
                    mentions=ent.get("mentions", []),
                    confidence=ent.get("confidence", 0.9),
                    needs_review=ent.get("needs_review", False),
                    metadata={"pii_anonymized": len(pii_data) > 0}
                )
                entities.append(entity)
            
            # Parse relations
            for rel in data.get("relations", []):
                relation = Relation(
                    source_entity=rel.get("source_entity", ""),
                    target_entity=rel.get("target_entity", ""),
                    relation_type=RelationType(rel.get("relation_type", "участвует_в")),
                    description=rel.get("description"),
                    confidence=rel.get("confidence", 0.9),
                    needs_review=rel.get("needs_review", False),
                    metadata={}
                )
                relations.append(relation)
                
        except (json.JSONDecodeError, ValueError) as e:
            # If parsing fails, try rule-based extraction
            entities, relations = self._rule_based_extraction(response, pii_data)
        
        return entities, relations
    
    def _rule_based_extraction(
        self, 
        text: str, 
        pii_data: List[PIIData]
    ) -> Tuple[List[Entity], List[Relation]]:
        """Fallback rule-based entity extraction"""
        
        entities = []
        relations = []
        
        # Marxist keywords for entity detection
        class_keywords = [
            "буржуазия", "пролетариат", "крестьянство", "рабочий класс",
            "класс эксплуататоров", "класс угнетенных", "мелкая буржуазия",
            "люмпенизированные слои", "аристократия", "феодалы"
        ]
        
        epoch_keywords = [
            "феодализм", "капитализм", "социализм", "коммунизм",
            "рабовладельческий строй", "первобытный строй",
            "эпоха", "период", "времена"
        ]
        
        production_keywords = [
            "капиталистический способ производства", "феодальный способ производства",
            "социалистическое производство", "товарное производство",
            "общественное производство", "способ производства"
        ]
        
        concept_keywords = [
            "прибавочная стоимость", "отчуждение", "эксплуатация",
            "классовая борьба", "производительные силы", "производственные отношения",
            "базис", "надстройка", "идеология", "материализм", "диалектика"
        ]
        
        # Simple pattern matching
        sentences = text.split('.')
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Check for class entities
            for keyword in class_keywords:
                if keyword.lower() in sentence.lower():
                    entities.append(Entity(
                        name=keyword,
                        entity_type=EntityType.CLASS,
                        description=f"Упоминание класса в контексте: {sentence[:100]}",
                        mentions=[keyword],
                        confidence=0.7,
                        needs_review=True,
                        metadata={"extraction_method": "rule_based"}
                    ))
            
            # Check for epoch entities
            for keyword in epoch_keywords:
                if keyword.lower() in sentence.lower():
                    entities.append(Entity(
                        name=keyword,
                        entity_type=EntityType.EPOCH,
                        description=f"Упоминание эпохи в контексте: {sentence[:100]}",
                        mentions=[keyword],
                        confidence=0.7,
                        needs_review=True,
                        metadata={"extraction_method": "rule_based"}
                    ))
            
            # Check for production modes
            for keyword in production_keywords:
                if keyword.lower() in sentence.lower():
                    entities.append(Entity(
                        name=keyword,
                        entity_type=EntityType.MODE_OF_PRODUCTION,
                        description=f"Упоминание способа производства: {sentence[:100]}",
                        mentions=[keyword],
                        confidence=0.7,
                        needs_review=True,
                        metadata={"extraction_method": "rule_based"}
                    ))
            
            # Check for concepts
            for keyword in concept_keywords:
                if keyword.lower() in sentence.lower():
                    entities.append(Entity(
                        name=keyword,
                        entity_type=EntityType.CONCEPT,
                        description=f"Упоминание понятия: {sentence[:100]}",
                        mentions=[keyword],
                        confidence=0.7,
                        needs_review=True,
                        metadata={"extraction_method": "rule_based"}
                    ))
        
        # Create basic relations based on co-occurrence
        classes = [e for e in entities if e.entity_type == EntityType.CLASS]
        epochs = [e for e in entities if e.entity_type == EntityType.EPOCH]
        
        for cls in classes:
            for epoch in epochs:
                relations.append(Relation(
                    source_entity=cls.name,
                    target_entity=epoch.name,
                    relation_type=RelationType.BELONGS_TO,
                    description="Предполагаемая связь на основе совместного упоминания",
                    confidence=0.5,
                    needs_review=True,
                    metadata={"extraction_method": "co_occurrence"}
                ))
        
        return entities, relations
    
    def anonymize_pii(self, text: str) -> Tuple[str, List[PIIData]]:
        """
        Detect and anonymize PII data in text
        
        Returns:
            Tuple of (anonymized_text, list of detected PII)
        """
        pii_data = []
        anonymized_text = text
        
        for pii_type, pattern in self.pii_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                start_pos = match.start()
                end_pos = match.end()
                value = match.group()
                
                # Create replacement
                if pii_type == 'email':
                    replacement = "[EMAIL]"
                elif pii_type == 'phone':
                    replacement = "[PHONE]"
                elif pii_type == 'ip_address':
                    replacement = "[IP]"
                elif pii_type == 'credit_card':
                    replacement = "[CREDIT_CARD]"
                elif pii_type == 'ssn':
                    replacement = "[SSN]"
                else:
                    replacement = f"[{pii_type.upper()}]"
                
                pii_data.append(PIIData(
                    type=pii_type,
                    value=value,
                    start_pos=start_pos,
                    end_pos=end_pos,
                    replacement=replacement
                ))
        
        # Replace PII in text (in reverse order to preserve positions)
        for pii in sorted(pii_data, key=lambda x: x.start_pos, reverse=True):
            anonymized_text = (
                anonymized_text[:pii.start_pos] + 
                pii.replacement + 
                anonymized_text[pii.end_pos:]
            )
        
        return anonymized_text, pii_data
    
    def deduplicate_entities(
        self, 
        entities: List[Entity], 
        threshold: float = 0.85
    ) -> List[Entity]:
        """
        Deduplicate entities using fuzzy matching and vector similarity
        
        Args:
            entities: List of entities to deduplicate
            threshold: Similarity threshold for considering duplicates
            
        Returns:
            Deduplicated list of entities
        """
        if not entities:
            return entities
        
        unique_entities = []
        
        for entity in entities:
            is_duplicate = False
            
            for unique_entity in unique_entities:
                # Check exact name match
                if entity.name.lower() == unique_entity.name.lower():
                    # Merge mentions
                    for mention in entity.mentions:
                        if mention not in unique_entity.mentions:
                            unique_entity.mentions.append(mention)
                    
                    # Keep higher confidence
                    if entity.confidence > unique_entity.confidence:
                        unique_entity.confidence = entity.confidence
                    
                    # Flag for review if conflicted
                    if entity.needs_review or unique_entity.needs_review:
                        unique_entity.needs_review = True
                    
                    is_duplicate = True
                    break
                
                # Check fuzzy match (simple Levenshtein-like heuristic)
                similarity = self._string_similarity(entity.name, unique_entity.name)
                if similarity >= threshold:
                    # Merge entities
                    for mention in entity.mentions:
                        if mention not in unique_entity.mentions:
                            unique_entity.mentions.append(mention)
                    
                    unique_entity.confidence = max(
                        unique_entity.confidence, 
                        entity.confidence
                    ) * 0.95  # Slight penalty for fuzzy match
                    
                    unique_entity.needs_review = True
                    unique_entity.metadata["fuzzy_match"] = True
                    unique_entity.metadata["similarity_score"] = similarity
                    
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_entities.append(entity)
        
        return unique_entities
    
    def _string_similarity(self, s1: str, s2: str) -> float:
        """Calculate simple string similarity ratio"""
        s1, s2 = s1.lower(), s2.lower()
        
        if s1 == s2:
            return 1.0
        
        len1, len2 = len(s1), len(s2)
        if len1 == 0 or len2 == 0:
            return 0.0
        
        # Simple character-based similarity
        common_chars = sum(1 for c in s1 if c in s2)
        similarity = (2.0 * common_chars) / (len1 + len2)
        
        return min(similarity, 1.0)


# Singleton instance
_extractor_instance: Optional[EntityExtractor] = None


def get_entity_extractor() -> EntityExtractor:
    """Get or create entity extractor instance"""
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = EntityExtractor()
    return _extractor_instance
