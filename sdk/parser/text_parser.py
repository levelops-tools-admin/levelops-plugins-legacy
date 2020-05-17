from enum import Enum

class SectionType(Enum):
    METADATA = 0
    ISSUES = 1
    ISSUE = 2
    

class Section(object):
    def __init__(self, section_type: SectionType, section_start, section_end, sub_section, section_parser=None, parent_section=None):
        self.section_type = section_type
        self.section_start = section_start
        self.section_end = section_end
        self.sub_section = sub_section
        self.section_parser = section_parser
        self.parent_section = parent_section
        self.completed = False
    
    def parse(self, line:str, contents: list):
        return self.section_parser(line, contents)


class SectionedTextParser(object):
    def __init__(self, sections: list, file_location: str, ignore_line):
        self.file_location = file_location
        self.sections = sections
        self.completed_sections = []
        self.current_section = None
        self.previous_section = None
        self.next_section = sections[0]
        self.current_parent_section = None
        self.section_contents = []
        self.previous_line = None
        self.ignore_line = ignore_line
        self.keep_parsing = True
        self.report = {
            'data': {}, 
            'summary': {}, 
            'aggregations': {
                'by_risk': {},
                'by_category': {},
                'by_impact': {},
                'by_exploitability': {},
                'by_component': {}
            }, 
            'metadata': {}
        }

    def parse(self):
        with open(self.file_location) as file:
            line = file.readline()
            while line:
                line = line.strip()
                if len(line) > 0 and not self.ignore_line(line):
                    self.parse_line(line)
                if not self.keep_parsing:
                    return self.report
                line = file.readline()
        return self.report

    def parse_line(self, line):
        content_section = self.current_section
        if not self.is_new_section(line) and not self.is_end_of_section(line):
            self.section_contents.append(line)
            self.previous_line = line
            return
        # what if no new section was detected but end of section was... next loop... what happens?
        if content_section and not content_section.completed:
            self.process_section(line, content_section)
        self.section_contents = []
        self.section_contents.append(line)
        if not self.next_section:
            self.keep_parsing = False

    def is_new_section(self, line):
        # if the current section is an issue then check if we are at the start of a new issue
        if self.current_section and self.current_section.section_type == SectionType.ISSUE:
            if self.current_section.section_start(line, self.previous_line, self.section_contents, self.completed_sections):
                self.previous_section = self.current_section
                return True
        # if we are not at the start of a new issue or the current section is not an issue check for the next section's start
        if self.next_section.section_start(line, self.previous_line, self.section_contents, self.completed_sections):
            self.previous_section = self.current_section
            self.current_section = self.next_section
            self.next_section = None
            if self.current_section and self.current_section.section_type == SectionType.ISSUES:
                self.next_section = self.current_section.sub_section
                self.next_section.parent_section = self.current_section
                return True
            if self.previous_section and self.previous_section.section_type == SectionType.ISSUES:
                self.next_section = self.current_section
                self.current_parent_section = self.previous_section
                return True
            if self.current_section and self.current_section.section_type == SectionType.ISSUE:
                return True
            if self.current_section and self.current_section.sub_section:
                self.next_section = self.current_section.sub_section
                return True
            for section in self.sections:
                if section != self.current_section and not section.completed:
                    self.next_section = section
                    break
            return True
        return False

    def is_end_of_section(self, line):
        if self.current_section and self.current_section.section_end(line, self.previous_line, self.section_contents, self.completed_sections):
            if self.current_section.section_type == SectionType.ISSUE:
                self.previous_section = self.current_section
            else:
                self.previous_section = self.current_section
                self.next_section = None
                if self.current_section and self.current_section.sub_section:
                    self.next_section = self.current_section.sub_section
                    return True
                for section in self.sections:
                    if section != self.current_section and not section.completed:
                        self.next_section = section
                        break
            return True
        if self.current_parent_section and self.current_parent_section.section_end(line, self.previous_line, self.section_contents, self.completed_sections):
            self.previous_section = self.current_parent_section
            self.next_section = None
            if self.current_section and self.current_section.sub_section:
                self.next_section = self.current_section.sub_section
                return True
            for section in self.sections:
                if section != self.current_section and not section.completed:
                    self.next_section = section
                    break
            return True
        return False

    def process_section(self, line, section):
        if section.parent_section:
            # if the section is a subsection, it will be marked as completed only at the end of the section
            # works for now since only issues -> issue but will have to change to be more generic and
            # handle sections with multiple sub sections
            if section.parent_section.section_end(line, self.previous_line, self.section_contents, self.completed_sections):
                section.parent_section.completed = True
                self.completed_sections.append(section.parent_section)
                section.completed = True
                self.completed_sections.append(section)
        elif section and not section.sub_section:
            # if the section doesn't have a parent nor sub_sections, directly mark it as completed
            section.completed = True
            self.completed_sections.append(section)
        # Only sections that group other sections will not have parser
        # these sections will be completed once the last sub section is completed
        # by the previous condition
        if not section or not section.section_parser:
            return
        
        section_name, data = section.parse(line, self.section_contents)
        self.report[section_name].update(data)
        if section and section.section_type == SectionType.ISSUE:
            self.report[section_name].update(data)
            for key in data:
                issue = data[key]
                risk_total = self.report['summary'].get('total_' + issue['risk'], 0)
                self.report['summary']['total_' + issue['risk']] = risk_total + 1
                by_risk = self.report['aggregations']['by_risk'].get(issue['risk'], 0)
                self.report['aggregations']['by_risk'][issue['risk']] = by_risk + 1
                if issue.get('category', None):
                    by_category = self.report['aggregations']['by_category'].get(issue['category'], 0)
                    self.report.get('aggregations')['by_category'][issue['category']] = by_category + 1
                if issue.get('exploitability', None):
                    by_exploitability = self.report['aggregations']['by_exploitability'].get(issue['exploitability'], 0)
                    self.report.get('aggregations')['by_exploitability'][issue['exploitability']] = by_exploitability + 1
                if issue.get('impact', None):
                    by_impact = self.report['aggregations']['by_impact'].get(issue['impact'], 0)
                    self.report.get('aggregations')['by_impact'][issue['impact']] = by_impact + 1
                if issue.get('component', None):
                    by_component = self.report['aggregations']['by_component'].get(issue['component'], 0)
                    self.report.get('aggregations')['by_component'][issue['component']] = by_component + 1
        #     return
        # self.report[''] = self.current_section.parse(self.section_contents)
